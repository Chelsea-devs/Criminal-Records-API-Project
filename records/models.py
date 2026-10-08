import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse

class Criminal(models.Model):
    class Gender(models.TextChoices):
        MALE='male','Male'; FEMALE='female','Female'; OTHER='other','Other'
    class Status(models.TextChoices):
        ACTIVE='active','Active'; WANTED='wanted','Wanted'; IN_CUSTODY='in_custody','In Custody'; RELEASED='released','Released'; CLOSED='closed','Case Closed'
    criminal_id=models.CharField(max_length=24,unique=True,editable=False,db_index=True)
    full_name=models.CharField(max_length=150,db_index=True)
    aliases=models.CharField(max_length=255,blank=True)
    gender=models.CharField(max_length=20,choices=Gender.choices)
    date_of_birth=models.DateField(null=True,blank=True)
    nationality=models.CharField(max_length=80,blank=True)
    phone_number=models.CharField(max_length=30,blank=True)
    email=models.EmailField(blank=True)
    last_known_location=models.CharField(max_length=255,db_index=True)
    residential_address=models.TextField(blank=True)
    occupation=models.CharField(max_length=120,blank=True)
    identification_number=models.CharField(max_length=100,blank=True)
    photo_url=models.URLField(blank=True, help_text='Legacy external photo URL (optional)')
    mugshot=models.ImageField(upload_to='mugshots/%Y/%m/',blank=True,null=True)
    risk_score=models.PositiveSmallIntegerField(default=20,validators=[MinValueValidator(0),MaxValueValidator(100)])
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE,db_index=True)
    is_repeat_offender=models.BooleanField(default=False)
    arrest_date=models.DateField(null=True,blank=True)
    release_date=models.DateField(null=True,blank=True)
    investigating_officer=models.CharField(max_length=150,blank=True)
    summary=models.TextField(blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name='created_criminal_records')
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['-created_at']; indexes=[models.Index(fields=['full_name','status']),models.Index(fields=['last_known_location'])]
    def save(self,*a,**k):
        if not self.criminal_id: self.criminal_id=f'CR-{uuid.uuid4().hex[:10].upper()}'
        super().save(*a,**k)
    def __str__(self): return f'{self.criminal_id} — {self.full_name}'
    def get_absolute_url(self): return reverse('criminal-detail',kwargs={'criminal_id':self.criminal_id})
    @property
    def charge_count(self): return self.charges.count()
    @property
    def active_charge_count(self): return self.charges.exclude(status=Charge.Status.DISMISSED).count()
    @property
    def total_fines(self): return sum((charge.fine_amount for charge in self.charges.all()), Decimal('0.00'))
    @property
    def map_query(self): return self.last_known_location or self.residential_address

class Charge(models.Model):
    class Severity(models.TextChoices):
        LOW='low','Low'; MODERATE='moderate','Moderate'; HIGH='high','High'; CRITICAL='critical','Critical'
    class Status(models.TextChoices):
        PENDING='pending','Pending'; UNDER_TRIAL='under_trial','Under Trial'; CONVICTED='convicted','Convicted'; ACQUITTED='acquitted','Acquitted'; DISMISSED='dismissed','Dismissed'
    criminal=models.ForeignKey(Criminal,on_delete=models.CASCADE,related_name='charges')
    offence=models.CharField(max_length=180,db_index=True); offence_code=models.CharField(max_length=60,blank=True)
    description=models.TextField(); severity=models.CharField(max_length=20,choices=Severity.choices,default=Severity.MODERATE)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    date_committed=models.DateField(null=True,blank=True); date_charged=models.DateField(null=True,blank=True)
    court_name=models.CharField(max_length=180,blank=True); case_number=models.CharField(max_length=100,blank=True,db_index=True)
    sentence=models.TextField(blank=True); fine_amount=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    prison_term_months=models.PositiveIntegerField(default=0); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=['-date_charged','-created_at']
    def __str__(self): return f'{self.offence} — {self.criminal.full_name}'

class Evidence(models.Model):
    class EvidenceType(models.TextChoices):
        DOCUMENT='document','Document'; IMAGE='image','Image'; VIDEO='video','Video'; AUDIO='audio','Audio'; PHYSICAL='physical','Physical'; DIGITAL='digital','Digital'; OTHER='other','Other'
    criminal=models.ForeignKey(Criminal,on_delete=models.CASCADE,related_name='evidence_items')
    charge=models.ForeignKey(Charge,null=True,blank=True,on_delete=models.SET_NULL,related_name='evidence_items')
    title=models.CharField(max_length=180); evidence_type=models.CharField(max_length=20,choices=EvidenceType.choices)
    description=models.TextField(blank=True); evidence_file=models.FileField(upload_to='evidence/%Y/%m/',blank=True,null=True)
    reference_url=models.URLField(blank=True); storage_reference=models.CharField(max_length=180,blank=True)
    collected_by=models.CharField(max_length=150,blank=True); collected_at=models.DateTimeField(null=True,blank=True)
    verified=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
    def __str__(self): return f'{self.title} — {self.criminal.criminal_id}'

class CaseNote(models.Model):
    criminal=models.ForeignKey(Criminal,on_delete=models.CASCADE,related_name='case_notes')
    title=models.CharField(max_length=180); body=models.TextField(); confidential=models.BooleanField(default=True)
    author=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE='create','Created'; UPDATE='update','Updated'; DELETE='delete','Deleted'; VIEW='view','Viewed'; LOGIN='login','Login'; EXPORT='export','Exported PDF'
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=20,choices=Action.choices)
    object_type=models.CharField(max_length=80); object_reference=models.CharField(max_length=180,blank=True)
    description=models.TextField(blank=True); ip_address=models.GenericIPAddressField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
    def __str__(self): return f'{self.get_action_display()} {self.object_type} {self.object_reference}'
