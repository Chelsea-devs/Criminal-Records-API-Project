from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.exceptions import NotFound

from .filters import CriminalFilter, ChargeFilter
from .models import Criminal, Charge, Evidence, CaseNote
from .permissions import AdminOnlyAPI
from .serializers import (
    CriminalListSerializer, CriminalDetailSerializer,
    ChargeSerializer, EvidenceSerializer, CaseNoteSerializer,
)


class CriminalViewSet(viewsets.ModelViewSet):
    lookup_field = "criminal_id"
    permission_classes = [AdminOnlyAPI]
    filterset_class = CriminalFilter
    search_fields = [
        "criminal_id", "full_name", "aliases", "nationality",
        "last_known_location", "identification_number",
        "investigating_officer", "charges__offence",
        "charges__case_number",
    ]
    ordering_fields = [
        "created_at", "updated_at", "full_name", "risk_score",
        "date_of_birth", "arrest_date",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Criminal.objects.select_related("created_by").prefetch_related(
            "charges", "evidence_items", "case_notes__author"
        ).annotate(
            charge_count_value=Count("charges", distinct=True)
        ).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return CriminalListSerializer
        return CriminalDetailSerializer

    @decorators.action(
        detail=True, methods=["get", "post"],
        permission_classes=[AdminOnlyAPI]
    )
    def charges(self, request, criminal_id=None):
        criminal = self.get_object()
        if request.method == "GET":
            serializer = ChargeSerializer(
                criminal.charges.all(), many=True,
                context={"request": request}
            )
            return response.Response(serializer.data)
        payload = request.data.copy()
        payload["criminal"] = criminal.pk
        serializer = ChargeSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criminal=criminal)
        return response.Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @decorators.action(
        detail=True, methods=["get", "post"],
        permission_classes=[AdminOnlyAPI]
    )
    def evidence(self, request, criminal_id=None):
        criminal = self.get_object()
        if request.method == "GET":
            return response.Response(
                EvidenceSerializer(criminal.evidence_items.all(), many=True).data
            )
        payload = request.data.copy()
        payload["criminal"] = criminal.pk
        serializer = EvidenceSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criminal=criminal)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=True, methods=["get", "post"],
        permission_classes=[AdminOnlyAPI]
    )
    def notes(self, request, criminal_id=None):
        criminal = self.get_object()
        if request.method == "GET":
            notes = criminal.case_notes.all()
            if not request.user.is_staff:
                notes = notes.filter(confidential=False)
            return response.Response(
                CaseNoteSerializer(notes, many=True).data
            )
        payload = request.data.copy()
        payload["criminal"] = criminal.pk
        serializer = CaseNoteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criminal=criminal, author=request.user)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)


class ChargeViewSet(viewsets.ModelViewSet):
    queryset = Charge.objects.select_related("criminal").all()
    serializer_class = ChargeSerializer
    permission_classes = [AdminOnlyAPI]
    filterset_class = ChargeFilter
    search_fields = [
        "offence", "offence_code", "description", "court_name",
        "case_number", "criminal__criminal_id", "criminal__full_name",
    ]
    ordering_fields = [
        "date_charged", "date_committed", "created_at",
        "fine_amount", "prison_term_months",
    ]
    ordering = ["-date_charged", "-created_at"]


class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.select_related("criminal", "charge").all()
    serializer_class = EvidenceSerializer
    permission_classes = [AdminOnlyAPI]
    filterset_fields = ["criminal", "charge", "evidence_type", "verified"]
    search_fields = [
        "title", "description", "storage_reference",
        "criminal__criminal_id", "criminal__full_name",
    ]
    ordering_fields = ["created_at", "collected_at"]
    ordering = ["-created_at"]


class CaseNoteViewSet(viewsets.ModelViewSet):
    queryset = CaseNote.objects.select_related("criminal", "author").all()
    serializer_class = CaseNoteSerializer
    permission_classes = [AdminOnlyAPI]
    filterset_fields = ["criminal", "confidential", "author"]
    search_fields = ["title", "body", "criminal__criminal_id"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@decorators.api_view(["GET"])
@decorators.permission_classes([AdminOnlyAPI])
def statistics(request):
    criminals = Criminal.objects.all()
    charges = Charge.objects.all()
    return response.Response({
        "criminals": {
            "total": criminals.count(),
            "wanted": criminals.filter(status=Criminal.Status.WANTED).count(),
            "in_custody": criminals.filter(status=Criminal.Status.IN_CUSTODY).count(),
            "repeat_offenders": criminals.filter(is_repeat_offender=True).count(),
            "average_risk_score": round(
                criminals.aggregate(value=Avg("risk_score"))["value"] or 0, 2
            ),
        },
        "charges": {
            "total": charges.count(),
            "pending": charges.filter(status=Charge.Status.PENDING).count(),
            "under_trial": charges.filter(status=Charge.Status.UNDER_TRIAL).count(),
            "convicted": charges.filter(status=Charge.Status.CONVICTED).count(),
            "total_fines": charges.aggregate(value=Sum("fine_amount"))["value"] or 0,
        },
        "generated_at": timezone.now(),
    })
