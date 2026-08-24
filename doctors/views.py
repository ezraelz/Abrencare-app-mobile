from rest_framework import viewsets
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .services.doctorNotificationServices import DoctorNotificationService
from .models import (
    Specialty,
    Doctor,
    Qualification,
    DoctorAvailability,
)

from .serializers import (
    SpecialtySerializer,
    DoctorSerializer,
    DoctorRegisterSerializer,
    QualificationSerializer,
    DoctorAvailabilitySerializer,
)
import logging

logger = logging.getLogger(__name__)


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all().order_by("name")
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]


class DoctorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doctor = Doctor.objects.all()
        serializer = DoctorSerializer(doctor, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DoctorRegisterSerializer(data=request.data)
        if serializer.is_valid():
            doctor = serializer.save()
            try:
                DoctorNotificationService.notify_created(doctor)
            except Exception:
                logger.exception("Failed to send doctor creation notification.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        doctor = Doctor.objects.get(id=pk)
        serializer = DoctorSerializer(doctor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = DoctorSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QualificationViewSet(viewsets.ModelViewSet):
    queryset = Qualification.objects.select_related("doctor")
    serializer_class = QualificationSerializer
    permission_classes = [IsAuthenticated]


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.select_related("doctor")
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    