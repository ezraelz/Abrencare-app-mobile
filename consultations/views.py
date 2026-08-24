from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated

from .models import Consultation, Prescription
from .serializers import (
    ConsultationSerializer,
    PrescriptionSerializer,
)


class ConsultationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        consultation = Consultation.objects.all()
        serializer = ConsultationSerializer(consultation, many=True)
        return Response(serializer.data, staus=status.HTTP_200_OK)

    def post(self, request):
        serializer = ConsultationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PrescriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prescription = Prescription.objects.all()
        serializer = PrescriptionSerializer(prescription, many=True)
        return Response(serializer.data, staus=status.HTTP_200_OK)

    def post(self, request):
        serializer = PrescriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    