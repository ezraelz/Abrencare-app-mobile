from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import (
    Specialty,
    Doctor,
    Qualification,
    DoctorAvailability,
)

from .serializers import (
    SpecialtySerializer,
    DoctorSerializer,
    QualificationSerializer,
    DoctorAvailabilitySerializer,
)


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all().order_by("name")
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related(
        "user",
        "specialty"
    ).prefetch_related(
        "qualifications"
    )
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]


class QualificationViewSet(viewsets.ModelViewSet):
    queryset = Qualification.objects.select_related("doctor")
    serializer_class = QualificationSerializer
    permission_classes = [IsAuthenticated]


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.select_related("doctor")
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    