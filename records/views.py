from io import BytesIO
from urllib.parse import quote_plus
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Avg,Q,Sum,Count
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from .forms import CriminalForm,ChargeForm,EvidenceForm,CaseNoteForm
from .models import Criminal,Charge,AuditLog

class CustomLoginView(LoginView):
    template_name='registration/login.html'; redirect_authenticated_user=True
    def get_success_url(self): return '/dashboard/' if self.request.user.is_staff else '/criminals/'

def _ip(request): return request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
def log(request,action,obj_type,ref='',desc=''):
    if request.user.is_authenticated: AuditLog.objects.create(actor=request.user,action=action,object_type=obj_type,object_reference=ref,description=desc,ip_address=_ip(request))

def logout_view(request):
    logout(request); messages.success(request,'You have been signed out securely.'); return redirect('home')

def home(request):
    records=Criminal.objects.prefetch_related('charges').all()[:12]
    return render(request,'records/home.html',{'records':records})

@staff_member_required(login_url='login')
def dashboard(request):
    criminals=Criminal.objects.prefetch_related('charges'); charges=Charge.objects.select_related('criminal')
    year=timezone.localdate().year
    rows=criminals.filter(created_at__year=year).annotate(month=ExtractMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month')
    monthly=[0]*12
    for row in rows: monthly[row['month']-1]=row['total']
    context={'total_criminals':criminals.count(),'wanted':criminals.filter(status='wanted').count(),'in_custody':criminals.filter(status='in_custody').count(),'repeat_offenders':criminals.filter(is_repeat_offender=True).count(),'total_charges':charges.count(),'convictions':charges.filter(status='convicted').count(),'total_fines':charges.aggregate(total=Sum('fine_amount'))['total'] or 0,'average_risk':round(criminals.aggregate(avg=Avg('risk_score'))['avg'] or 0,1),'recent_records':criminals[:7],'high_risk':criminals.filter(risk_score__gte=70)[:6],'monthly_data':monthly,'analysis_year':year,'audit_logs':AuditLog.objects.select_related('actor')[:8]}
    return render(request,'records/dashboard.html',context)

def criminal_list(request):
    qs=Criminal.objects.prefetch_related('charges').all(); search=request.GET.get('q','').strip(); status=request.GET.get('status','').strip(); gender=request.GET.get('gender','').strip()
    if search: qs=qs.filter(Q(criminal_id__icontains=search)|Q(full_name__icontains=search)|Q(aliases__icontains=search)|Q(last_known_location__icontains=search)|Q(charges__offence__icontains=search)|Q(charges__case_number__icontains=search)).distinct()
    if status: qs=qs.filter(status=status)
    if gender: qs=qs.filter(gender=gender)
    return render(request,'records/criminal_list.html',{'criminals':qs,'q':search,'selected_status':status,'selected_gender':gender,'statuses':Criminal.Status.choices,'genders':Criminal.Gender.choices})

def case_file_search(request):
    query=request.GET.get('case','').strip()
    results=Charge.objects.select_related('criminal').none()
    searched=False
    if query:
        searched=True
        results=Charge.objects.select_related('criminal').filter(
            Q(case_number__icontains=query)
            | Q(criminal__criminal_id__icontains=query)
            | Q(criminal__full_name__icontains=query)
            | Q(criminal__aliases__icontains=query)
            | Q(offence__icontains=query)
        ).order_by('-date_charged','-created_at').distinct()
    return render(request,'records/case_file_search.html',{
        'query':query,'results':results,'searched':searched,
    })

def criminal_detail(request,criminal_id):
    criminal=get_object_or_404(Criminal.objects.prefetch_related('charges','evidence_items','case_notes__author'),criminal_id=criminal_id)
    notes=criminal.case_notes.all() if request.user.is_staff else criminal.case_notes.filter(confidential=False)
    return render(request,'records/criminal_detail.html',{'criminal':criminal,'notes':notes,'map_url':'https://www.google.com/maps/search/?api=1&query='+quote_plus(criminal.map_query)})

@staff_member_required(login_url='login')
def criminal_create(request):
    form=CriminalForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            obj=form.save(commit=False); obj.created_by=request.user; obj.save(); charge=form.save_charge(obj)
            log(request,'create','Criminal',obj.criminal_id,obj.full_name)
            if charge: log(request,'create','Charge',str(charge.pk),f'{charge.offence} / {obj.criminal_id}')
        messages.success(request,'Record and charge created successfully.' if charge else 'Record created.'); return redirect(obj)
    return render(request,'records/form.html',{'form':form,'title':'Create criminal record','subtitle':'Identity and investigation profile','multipart':True})
@staff_member_required(login_url='login')
def criminal_update(request,criminal_id):
    obj=get_object_or_404(Criminal,criminal_id=criminal_id); form=CriminalForm(request.POST or None,request.FILES or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            form.save(); charge=form.save_charge(obj)
            log(request,'update','Criminal',obj.criminal_id,obj.full_name)
            if charge: log(request,'create','Charge',str(charge.pk),f'{charge.offence} / {obj.criminal_id}')
        messages.success(request,'Record updated and new charge added.' if charge else 'Record updated.'); return redirect(obj)
    return render(request,'records/form.html',{'form':form,'title':f'Update {obj.full_name}','subtitle':obj.criminal_id,'multipart':True})
@staff_member_required(login_url='login')
def criminal_delete(request,criminal_id):
    obj=get_object_or_404(Criminal,criminal_id=criminal_id)
    if request.method=='POST': ref=obj.criminal_id; name=obj.full_name; obj.delete(); log(request,'delete','Criminal',ref,name); messages.success(request,'Record deleted.'); return redirect('criminal-list')
    return render(request,'records/confirm_delete.html',{'object':obj,'object_type':'criminal record'})
@staff_member_required(login_url='login')
def charge_create(request,criminal_id):
    criminal=get_object_or_404(Criminal,criminal_id=criminal_id); form=ChargeForm(request.POST or None)
    if request.method=='POST' and form.is_valid(): obj=form.save(commit=False); obj.criminal=criminal; obj.save(); log(request,'create','Charge',str(obj.pk),f'{obj.offence} / {criminal.criminal_id}'); messages.success(request,'Charge added.'); return redirect(criminal)
    return render(request,'records/form.html',{'form':form,'title':f'Add charge — {criminal.full_name}','subtitle':criminal.criminal_id})
@staff_member_required(login_url='login')
def charge_update(request,pk):
    obj=get_object_or_404(Charge,pk=pk); form=ChargeForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid(): form.save(); log(request,'update','Charge',str(obj.pk),obj.offence); messages.success(request,'Charge updated.'); return redirect(obj.criminal)
    return render(request,'records/form.html',{'form':form,'title':f'Update charge — {obj.offence}','subtitle':obj.criminal.criminal_id})
@staff_member_required(login_url='login')
def charge_delete(request,pk):
    obj=get_object_or_404(Charge,pk=pk); criminal=obj.criminal
    if request.method=='POST': ref=str(obj.pk); desc=obj.offence; obj.delete(); log(request,'delete','Charge',ref,desc); messages.success(request,'Charge deleted.'); return redirect(criminal)
    return render(request,'records/confirm_delete.html',{'object':obj,'object_type':'charge'})
@staff_member_required(login_url='login')
def evidence_create(request,criminal_id):
    criminal=get_object_or_404(Criminal,criminal_id=criminal_id); form=EvidenceForm(request.POST or None,request.FILES or None); form.fields['charge'].queryset=criminal.charges.all()
    if request.method=='POST' and form.is_valid(): obj=form.save(commit=False); obj.criminal=criminal; obj.save(); log(request,'create','Evidence',str(obj.pk),obj.title); messages.success(request,'Evidence uploaded.'); return redirect(criminal)
    return render(request,'records/form.html',{'form':form,'title':f'Upload evidence — {criminal.full_name}','subtitle':criminal.criminal_id,'multipart':True})
@staff_member_required(login_url='login')
def note_create(request,criminal_id):
    criminal=get_object_or_404(Criminal,criminal_id=criminal_id); form=CaseNoteForm(request.POST or None)
    if request.method=='POST' and form.is_valid(): obj=form.save(commit=False); obj.criminal=criminal; obj.author=request.user; obj.save(); log(request,'create','CaseNote',str(obj.pk),obj.title); messages.success(request,'Case note added.'); return redirect(criminal)
    return render(request,'records/form.html',{'form':form,'title':f'Add case note — {criminal.full_name}','subtitle':criminal.criminal_id})

@staff_member_required(login_url='login')
def criminal_pdf(request,criminal_id):
    c=get_object_or_404(Criminal.objects.prefetch_related('charges','evidence_items','case_notes'),criminal_id=criminal_id)
    response=HttpResponse(content_type='application/pdf'); response['Content-Disposition']=f'attachment; filename="{c.criminal_id}_report.pdf"'
    doc=SimpleDocTemplate(response,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='Small',parent=styles['BodyText'],fontSize=8,leading=11))
    story=[Paragraph('CRIMINAL RECORD INTELLIGENCE REPORT',styles['Title']),Paragraph(f'{c.criminal_id} — {c.full_name}',styles['Heading1']),Spacer(1,8)]
    data=[['Status',c.get_status_display()],['Risk score',f'{c.risk_score}/100'],['Gender',c.get_gender_display()],['Aliases',c.aliases or '—'],['Nationality',c.nationality or '—'],['Last known location',c.last_known_location],['Investigating officer',c.investigating_officer or '—'],['Repeat offender','Yes' if c.is_repeat_offender else 'No'],['Total fines',f'NGN {c.total_fines:,.2f}']]
    t=Table(data,colWidths=[45*mm,110*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#10242d')),('TEXTCOLOR',(0,0),(0,-1),colors.white),('GRID',(0,0),(-1,-1),.4,colors.grey),('PADDING',(0,0),(-1,-1),6)])); story += [t,Spacer(1,14),Paragraph('Case Summary',styles['Heading2']),Paragraph(c.summary or 'No summary recorded.',styles['BodyText']),Spacer(1,12),Paragraph('Charges',styles['Heading2'])]
    if c.charges.exists():
        rows=[['Offence','Severity','Status','Case number','Court','Fine (NGN)']]+[[x.offence,x.get_severity_display(),x.get_status_display(),x.case_number or '—',x.court_name or '—',f'{x.fine_amount:,.2f}'] for x in c.charges.all()]
        tt=Table(rows,repeatRows=1,colWidths=[36*mm,18*mm,24*mm,26*mm,36*mm,25*mm]); tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#167c77')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.35,colors.grey),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),4)])); story.append(tt)
    else: story.append(Paragraph('No charges recorded.',styles['BodyText']))
    story += [Spacer(1,12),Paragraph('Evidence Register',styles['Heading2'])]
    for e in c.evidence_items.all(): story.append(Paragraph(f'• {e.title} ({e.get_evidence_type_display()}) — {"Verified" if e.verified else "Pending"}',styles['Small']))
    story += [Spacer(1,18),Paragraph(f'Generated {timezone.localtime():%d %B %Y, %H:%M} by {request.user.get_username()}',styles['Small'])]
    doc.build(story); log(request,'export','Criminal',c.criminal_id,'PDF report'); return response
