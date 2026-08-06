from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Feature, Service
from .serializers import (
    FeatureSerializer,
    ServiceSerializer,
)


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all().order_by("feature_name")
    serializer_class = FeatureSerializer
    permission_classes = [IsAuthenticated]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.prefetch_related("features").order_by("service_name")
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
