from rest_framework import serializers
from .models import Appointment, Scheduling
from patients.models import Patient
from doctors.models import Doctor


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="patient.user.get_full_name",
        read_only=True
    )
    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name",
        read_only=True
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "appointment_date",
            "appointment_time",
            "status",
            "reason",
            "created_at",
        ]
        read_only_fields = ("created_at",)


class SchedulingSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name",
        read_only=True
    )

    class Meta:
        model = Scheduling
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "day",
            "start_time",
            "end_time",
            "is_available",
            "created_at",
        ]
        read_only_fields = ("created_at",)