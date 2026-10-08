from django.contrib import admin
from .models import Criminal, Charge, Evidence, CaseNote, AuditLog


class ChargeInline(admin.TabularInline):
    model = Charge
    extra = 1
    fields = [
        "offence", "description", "severity", "status", "date_charged",
        "court_name", "case_number", "fine_amount",
    ]


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    fields = ["title", "evidence_type", "verified", "collected_at"]


@admin.register(Criminal)
class CriminalAdmin(admin.ModelAdmin):
    list_display = [
        "criminal_id", "full_name", "gender", "status",
        "risk_score", "is_repeat_offender", "charge_total", "fine_total", "updated_at",
    ]
    list_filter = [
        "status", "gender", "is_repeat_offender",
        "nationality", "created_at",
    ]
    search_fields = [
        "criminal_id", "full_name", "aliases", "last_known_location",
        "identification_number", "charges__offence", "charges__case_number",
    ]
    readonly_fields = ["criminal_id", "created_at", "updated_at"]
    inlines = [ChargeInline, EvidenceInline]
    fieldsets = (
        ("Identity", {
            "fields": (
                "criminal_id", "full_name", "aliases", "gender",
                "date_of_birth", "nationality", "photo_url",
            )
        }),
        ("Contact and location", {
            "fields": (
                "phone_number", "email", "last_known_location",
                "residential_address", "occupation", "identification_number",
            )
        }),
        ("Risk and case status", {
            "fields": (
                "risk_score", "status", "is_repeat_offender",
                "arrest_date", "release_date", "investigating_officer",
                "summary",
            )
        }),
        ("Audit", {
            "fields": ("created_by", "created_at", "updated_at")
        }),
    )

    @admin.display(description="Charges")
    def charge_total(self, obj):
        return obj.charges.count()

    @admin.display(description="Total fines (NGN)")
    def fine_total(self, obj):
        return f"₦{obj.total_fines:,.2f}"


@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = [
        "offence", "criminal", "severity", "status",
        "date_charged", "case_number", "fine_amount",
    ]
    list_filter = ["severity", "status", "date_charged", "court_name"]
    search_fields = [
        "offence", "case_number", "criminal__criminal_id",
        "criminal__full_name",
    ]
    autocomplete_fields = ["criminal"]


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = [
        "title", "criminal", "evidence_type", "verified",
        "collected_by", "created_at",
    ]
    list_filter = ["evidence_type", "verified", "created_at"]
    search_fields = [
        "title", "criminal__criminal_id", "criminal__full_name",
        "storage_reference",
    ]


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ["title", "criminal", "author", "confidential", "created_at"]
    list_filter = ["confidential", "created_at"]
    search_fields = ["title", "body", "criminal__criminal_id"]

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display=['created_at','actor','action','object_type','object_reference','ip_address']
    list_filter=['action','object_type','created_at']
    search_fields=['actor__username','object_reference','description']
    readonly_fields=['actor','action','object_type','object_reference','description','ip_address','created_at']
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
