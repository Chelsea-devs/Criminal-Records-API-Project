import django_filters
from .models import Criminal, Charge


class CriminalFilter(django_filters.FilterSet):
    min_risk = django_filters.NumberFilter(field_name="risk_score", lookup_expr="gte")
    max_risk = django_filters.NumberFilter(field_name="risk_score", lookup_expr="lte")
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    has_charges = django_filters.BooleanFilter(method="filter_has_charges")

    class Meta:
        model = Criminal
        fields = [
            "gender", "status", "nationality", "is_repeat_offender",
            "investigating_officer",
        ]

    def filter_has_charges(self, queryset, name, value):
        if value is True:
            return queryset.filter(charges__isnull=False).distinct()
        if value is False:
            return queryset.filter(charges__isnull=True)
        return queryset


class ChargeFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="date_charged", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date_charged", lookup_expr="lte")
    criminal_id = django_filters.CharFilter(field_name="criminal__criminal_id")

    class Meta:
        model = Charge
        fields = ["severity", "status", "court_name", "case_number"]
