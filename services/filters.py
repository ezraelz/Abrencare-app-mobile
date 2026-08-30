import django_filters

from .models import Service, ServiceAudience


class ServiceFilter(django_filters.FilterSet):
    service_for = django_filters.ChoiceFilter(choices=ServiceAudience.choices)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Service
        fields = ["service_for", "is_active"]
