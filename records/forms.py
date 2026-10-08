from decimal import Decimal

from django import forms
from .models import Criminal, Charge, Evidence, CaseNote
class DateInput(forms.DateInput): input_type='date'
class DateTimeInput(forms.DateTimeInput): input_type='datetime-local'
class CriminalForm(forms.ModelForm):
    charge_offence=forms.CharField(required=False,label='Charges / offence',max_length=180,widget=forms.TextInput(attrs={'placeholder':'For example: Financial fraud'}))
    charge_description=forms.CharField(required=False,label='Charge description',widget=forms.Textarea(attrs={'rows':3,'placeholder':'Describe the charge or offence'}))
    charge_severity=forms.ChoiceField(required=False,label='Charge severity',choices=Charge.Severity.choices,initial=Charge.Severity.MODERATE)
    charge_status=forms.ChoiceField(required=False,label='Charge status',choices=Charge.Status.choices,initial=Charge.Status.PENDING)
    charge_case_number=forms.CharField(required=False,label='Charge case number',max_length=100,widget=forms.TextInput(attrs={'placeholder':'For example: FCT-2026-014'}))
    fine_amount=forms.DecimalField(required=False,label='Fine amount (₦)',min_value=Decimal('0.00'),max_digits=14,decimal_places=2,widget=forms.NumberInput(attrs={'min':'0','step':'0.01','placeholder':'0.00'}),help_text='Enter the fine in naira. Leave blank if no fine applies.')

    class Meta:
        model=Criminal
        exclude=['criminal_id','created_by','created_at','updated_at','photo_url']
        widgets={'date_of_birth':DateInput(),'arrest_date':DateInput(),'release_date':DateInput(),'summary':forms.Textarea(attrs={'rows':5}),'residential_address':forms.Textarea(attrs={'rows':3})}

    def clean(self):
        cleaned=super().clean()
        offence=(cleaned.get('charge_offence') or '').strip()
        details=(cleaned.get('charge_description') or '').strip() or (cleaned.get('charge_case_number') or '').strip()
        fine=cleaned.get('fine_amount')
        if not offence and (details or (fine is not None and fine > 0)):
            self.add_error('charge_offence','Enter a charge or offence before adding charge details or a fine.')
        return cleaned

    def save_charge(self,criminal):
        offence=(self.cleaned_data.get('charge_offence') or '').strip()
        if not offence:
            return None
        return Charge.objects.create(
            criminal=criminal,
            offence=offence,
            description=(self.cleaned_data.get('charge_description') or '').strip() or f'Charge recorded for {offence}.',
            severity=self.cleaned_data.get('charge_severity') or Charge.Severity.MODERATE,
            status=self.cleaned_data.get('charge_status') or Charge.Status.PENDING,
            case_number=(self.cleaned_data.get('charge_case_number') or '').strip(),
            fine_amount=self.cleaned_data.get('fine_amount') or Decimal('0.00'),
        )
class ChargeForm(forms.ModelForm):
    class Meta:
        model=Charge; exclude=['criminal','created_at','updated_at']
        widgets={'date_committed':DateInput(),'date_charged':DateInput(),'description':forms.Textarea(attrs={'rows':4}),'sentence':forms.Textarea(attrs={'rows':3})}
class EvidenceForm(forms.ModelForm):
    class Meta:
        model=Evidence; exclude=['criminal','created_at','reference_url']
        widgets={'collected_at':DateTimeInput(),'description':forms.Textarea(attrs={'rows':4})}
class CaseNoteForm(forms.ModelForm):
    class Meta:
        model=CaseNote; exclude=['criminal','author','created_at']; widgets={'body':forms.Textarea(attrs={'rows':5})}
