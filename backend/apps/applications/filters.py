from django_filters import rest_framework as filters

from .models import Application


class ApplicationFilter(filters.FilterSet):
    status = filters.CharFilter(field_name="status")
    job_type = filters.CharFilter(field_name="job_type")
    priority = filters.CharFilter(field_name="priority")
    source = filters.CharFilter(field_name="source")
    is_remote = filters.BooleanFilter(field_name="is_remote")
    applied_after = filters.DateFilter(field_name="applied_date", lookup_expr="gte")
    applied_before = filters.DateFilter(field_name="applied_date", lookup_expr="lte")
    tags = filters.CharFilter(method="filter_by_tags")

    class Meta:
        model = Application
        fields = [
            "status",
            "job_type",
            "priority",
            "source",
            "is_remote",
        ]

    def filter_by_tags(self, queryset, name, value):
        tag_ids = [int(id_) for id_ in value.split(",") if id_.strip().isdigit()]
        if tag_ids:
            return queryset.filter(tags__id__in=tag_ids).distinct()
        return queryset
