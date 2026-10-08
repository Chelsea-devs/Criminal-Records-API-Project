from decimal import Decimal

from django.db import transaction
from rest_framework import serializers
from .models import Criminal, Charge, Evidence, CaseNote


class ChargeSerializer(serializers.ModelSerializer):
    criminal_id = serializers.CharField(
        source="criminal.criminal_id", read_only=True
    )
    criminal_name = serializers.CharField(
        source="criminal.full_name", read_only=True
    )

    class Meta:
        model = Charge
        fields = [
            "id", "criminal", "criminal_id", "criminal_name",
            "offence", "offence_code", "description", "severity", "status",
            "date_committed", "date_charged", "court_name", "case_number",
            "sentence", "fine_amount", "prison_term_months",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class EvidenceSerializer(serializers.ModelSerializer):
    criminal_id = serializers.CharField(
        source="criminal.criminal_id", read_only=True
    )
    charge_offence = serializers.CharField(
        source="charge.offence", read_only=True, allow_null=True
    )

    class Meta:
        model = Evidence
        fields = [
            "id", "criminal", "criminal_id", "charge", "charge_offence",
            "title", "evidence_type", "description", "reference_url", "evidence_file",
            "storage_reference", "collected_by", "collected_at",
            "verified", "created_at",
        ]
        read_only_fields = ["created_at"]


class CaseNoteSerializer(serializers.ModelSerializer):
    criminal_id = serializers.CharField(
        source="criminal.criminal_id", read_only=True
    )
    author_name = serializers.CharField(
        source="author.get_full_name", read_only=True
    )

    class Meta:
        model = CaseNote
        fields = [
            "id", "criminal", "criminal_id", "title", "body",
            "confidential", "author", "author_name", "created_at",
        ]
        read_only_fields = ["author", "created_at"]


class CriminalListSerializer(serializers.ModelSerializer):
    charges = ChargeSerializer(many=True, read_only=True)
    charge_count = serializers.IntegerField(read_only=True)
    active_charge_count = serializers.IntegerField(read_only=True)
    total_fines = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = Criminal
        fields = [
            "id", "criminal_id", "full_name", "aliases", "gender",
            "date_of_birth", "nationality", "last_known_location",
            "photo_url", "mugshot", "risk_score", "status", "is_repeat_offender",
            "investigating_officer", "charge_count", "active_charge_count", "total_fines",
            "charges", "created_at", "updated_at",
        ]


class CriminalDetailSerializer(serializers.ModelSerializer):
    charges = ChargeSerializer(many=True, read_only=True)
    evidence_items = EvidenceSerializer(many=True, read_only=True)
    case_notes = CaseNoteSerializer(many=True, read_only=True)
    charge_count = serializers.IntegerField(read_only=True)
    active_charge_count = serializers.IntegerField(read_only=True)
    total_fines = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    charge_offence = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        label="Charges / offence",
        help_text="Enter the criminal charge to attach to this record.",
    )
    charge_description = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        label="Charge description",
        style={"base_template": "textarea.html"},
    )
    charge_severity = serializers.ChoiceField(
        choices=Charge.Severity.choices,
        required=False,
        allow_blank=True,
        write_only=True,
        label="Charge severity",
    )
    charge_status = serializers.ChoiceField(
        choices=Charge.Status.choices,
        required=False,
        allow_blank=True,
        write_only=True,
        label="Charge status",
    )
    charge_case_number = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        label="Charge case number",
    )
    fine_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        allow_null=True,
        write_only=True,
        label="Fine amount (NGN)",
        help_text="Enter the fine in naira; leave empty if there is no fine.",
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = Criminal
        fields = [
            "id", "criminal_id", "full_name", "aliases", "gender",
            "date_of_birth", "nationality", "phone_number", "email",
            "last_known_location", "residential_address", "occupation",
            "identification_number", "photo_url", "mugshot", "risk_score", "status",
            "is_repeat_offender", "arrest_date", "release_date",
            "investigating_officer", "summary", "charge_offence",
            "charge_description", "charge_severity", "charge_status",
            "charge_case_number", "fine_amount", "created_by",
            "created_by_name", "charge_count", "active_charge_count", "total_fines",
            "charges", "evidence_items", "case_notes",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "criminal_id", "created_by", "created_at", "updated_at"
        ]

    def validate(self, attrs):
        offence = attrs.get("charge_offence", "").strip()
        description = attrs.get("charge_description", "").strip()
        case_number = attrs.get("charge_case_number", "").strip()
        fine = attrs.get("fine_amount")

        if not offence and (description or case_number or (fine is not None and fine > 0)):
            raise serializers.ValidationError({
                "charge_offence": "Enter the charge or offence before adding charge details or a fine."
            })
        return attrs

    @staticmethod
    def _extract_charge(validated_data):
        return {
            "offence": validated_data.pop("charge_offence", "").strip(),
            "description": validated_data.pop("charge_description", "").strip(),
            "severity": validated_data.pop("charge_severity", "") or Charge.Severity.MODERATE,
            "status": validated_data.pop("charge_status", "") or Charge.Status.PENDING,
            "case_number": validated_data.pop("charge_case_number", "").strip(),
            "fine_amount": validated_data.pop("fine_amount", None) or Decimal("0.00"),
        }

    @staticmethod
    def _save_charge(criminal, charge_data):
        if charge_data["offence"]:
            if not charge_data["description"]:
                charge_data["description"] = f"Charge recorded for {charge_data['offence']}."
            Charge.objects.create(criminal=criminal, **charge_data)

    @transaction.atomic
    def create(self, validated_data):
        charge_data = self._extract_charge(validated_data)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        criminal = super().create(validated_data)
        self._save_charge(criminal, charge_data)
        return criminal

    @transaction.atomic
    def update(self, instance, validated_data):
        charge_data = self._extract_charge(validated_data)
        criminal = super().update(instance, validated_data)
        self._save_charge(criminal, charge_data)
        if hasattr(criminal, "_prefetched_objects_cache"):
            criminal._prefetched_objects_cache.pop("charges", None)
        return criminal
