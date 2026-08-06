from rest_framework import serializers
from .models import Consultation, Prescription


class ConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="appointment.patient.user.get_full_name",
        read_only=True,
    )

    doctor_name = serializers.CharField(
        source="appointment.doctor.user.get_full_name",
        read_only=True,
    )

    class Meta:
        model = Consultation
        fields = [
            "id",
            "appointment",
            "patient_name",
            "doctor_name",
            "diagnosis",
            "notes",
            "follow_up_date",
            "created_at",
        ]
        read_only_fields = ("created_at",)


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="consultation.appointment.patient.user.get_full_name",
        read_only=True,
    )

    doctor_name = serializers.CharField(
        source="consultation.appointment.doctor.user.get_full_name",
        read_only=True,
    )

    class Meta:
        model = Prescription
        fields = [
            "id",
            "consultation",
            "patient_name",
            "doctor_name",
            "medication",
            "dosage",
            "frequency",
            "duration",
            "instructions",
        ]
        