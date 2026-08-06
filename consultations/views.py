from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Consultation, Prescription
from .serializers import (
    ConsultationSerializer,
    PrescriptionSerializer,
)


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all().order_by("-created_at")
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]