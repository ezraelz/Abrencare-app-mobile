from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .models import (
    Patient,
    MedicalRecord,
    MedicalDocument,
)

from .serializers import (
    PatientSerializer,
    PatientRegisterSerializer,
    MedicalRecordSerializer,
    MedicalDocumentSerializer,
)
from .services.patientNotificationServices import PatientNotificationService

class PatientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patients = Patient.objects.all()
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PatientRegisterSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            PatientNotificationService.notify_created(patient)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        patients = Patient.objects.get(id=pk)
        serializer = PatientSerializer(patients)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = PatientSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.select_related(
        "patient__user",
        "doctor__user",
    ).order_by("-created_at")

    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]


class MedicalDocumentViewSet(viewsets.ModelViewSet):
    queryset = MedicalDocument.objects.select_related(
        "patient__user",
        "uploaded_by",
    ).order_by("-uploaded_at")

    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated]
    