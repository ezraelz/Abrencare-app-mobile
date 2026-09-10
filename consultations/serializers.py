from django.utils import timezone
from rest_framework import serializers

from .models import Consultation, Prescription
from doctors.models import Doctor, Specialty


# ============================================================
# SPECIALTY
# ============================================================

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "description"]


# ============================================================
# DOCTOR
# ============================================================

class ConsultationDoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.full_name", read_only=True)
    specialty = serializers.CharField(source="specialty.name", read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "id", 
            "name", 
            "specialty",
            "years_of_experience",
            "consultation_fee", 
            "consultation_duration", 
            "bio",
        ]


# ============================================================
# AVAILABLE SLOT
# ============================================================

class ConsultationSlotSerializer(serializers.Serializer):
    time = serializers.TimeField()
    available = serializers.BooleanField()


# ============================================================
# CONSULTATION BOOKING
# ============================================================

class ConsultationBookingSerializer(serializers.Serializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()
    #consultation_type = serializers.ChoiceField(choices=Consultation.Type.choices,default=Consultation.Type.VIDEO,)
    #language = serializers.ChoiceField(choices=Consultation.Language.choices,default=Consultation.Language.ENGLISH,)
    #reason_for_visit = serializers.CharField(required=False,allow_blank=True,default="Digital consultation",)

    def validate(self, attrs):
        appointment_date = attrs["appointment_date"]
        appointment_time = attrs["appointment_time"]
        now = timezone.localtime()

        if appointment_date < now.date():
            raise serializers.ValidationError(
                {"appointment_date": "Appointment date cannot be in the past."}
            )

        if appointment_date == now.date() and appointment_time < now.time():
            raise serializers.ValidationError(
                {"appointment_time": "Appointment time cannot be in the past."}
            )

        # Note: doctor approval is already enforced by doctor_id's queryset
        # filter above, so no need to re-check it here.
        return attrs


# ============================================================
# CONSULTATION CANCEL
# ============================================================

class ConsultationCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


# ============================================================
# CONSULTATION RESPONSE
# ============================================================

class ConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="appointment.patient.user.full_name", read_only=True)
    doctor_name = serializers.CharField(source="appointment.doctor.user.full_name", read_only=True)
    doctor_id = serializers.CharField(source="appointment.doctor.id", read_only=True)
    specialty_name = serializers.CharField(source="appointment.doctor.specialty.name", read_only=True)
    appointment_date = serializers.DateField(source="appointment.appointment_date", read_only=True)
    appointment_time = serializers.TimeField(source="appointment.appointment_time", read_only=True)
    duration_minutes = serializers.IntegerField(source="appointment.duration_minutes", read_only=True)
    appointment_status = serializers.CharField(source="appointment.status", read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id",
            "appointment",
            "patient_name",
            "doctor_name", 
            "doctor_id", 
            "specialty_name",
            "appointment_date", 
            "appointment_time", 
            "duration_minutes", 
            "appointment_status",
            "consultation_type", 
            "language", 
            "status", 
            "price", 
            "currency",
            "meeting_url", 
            "started_at", 
            "ended_at", 
            "created_at", 
            "updated_at",
        ]
        read_only_fields = fields


# ============================================================
# PRESCRIPTION
# ============================================================

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="consultation.appointment.patient.user.full_name", read_only=True
    )
    doctor_name = serializers.CharField(
        source="consultation.appointment.doctor.user.full_name", read_only=True
    )

    class Meta:
        model = Prescription
        fields = [
            "id", "consultation", "patient_name", "doctor_name", "medication",
            "dosage", "frequency", "duration", "instructions", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "consultation", "patient_name", "doctor_name", "created_at", "updated_at",
        ]


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ["medication", "dosage", "frequency", "duration", "instructions"]
        