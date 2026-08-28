from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(
    serializers.ModelSerializer
):

    patient_name = serializers.CharField(
        source="patient.user.full_name",
        read_only=True,
    )

    doctor_name = serializers.CharField(
        source="doctor.user.full_name",
        read_only=True,
    )

    doctor_specialty = serializers.CharField(
        source="doctor.specialty.name",
        read_only=True,
        allow_null=True,
    )

    end_time = serializers.TimeField(
        read_only=True,
    )

    class Meta:
        model = Appointment

        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "doctor_specialty",
            "appointment_date",
            "appointment_time",
            "end_time",
            "duration_minutes",
            "status",
            "reason_for_visit",
            "confirmed_at",
            "completed_at",
            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_name",
            "doctor_name",
            "doctor_specialty",
            "end_time",
            "duration_minutes",
            "status",
            "confirmed_at",
            "completed_at",
            "cancelled_at",
            "cancelled_by",
            "created_at",
            "updated_at",
        ]
        

class AppointmentCreateSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Appointment

        fields = [
            "doctor",
            "appointment_date",
            "appointment_time",
            "reason_for_visit",
        ]

    def validate(self, attrs):

        doctor = attrs["doctor"]
        appointment_date = attrs[
            "appointment_date"
        ]
        appointment_time = attrs[
            "appointment_time"
        ]

        today = timezone.localdate()

        if appointment_date < today:
            raise serializers.ValidationError({
                "appointment_date":
                    "Appointment date cannot be in the past."
            })

        duration = (
            doctor.consultation_duration_minutes
        )

        requested_start = datetime.combine(
            appointment_date,
            appointment_time,
        )

        requested_end = (
            requested_start
            + timedelta(minutes=duration)
        )

        weekday = appointment_date.strftime(
            "%A"
        ).lower()

        availability = doctor.availability.filter(
            day=weekday,
            is_available=True,
        )

        fits_schedule = False

        for window in availability:

            window_start = datetime.combine(
                appointment_date,
                window.start_time,
            )

            window_end = datetime.combine(
                appointment_date,
                window.end_time,
            )

            if (
                requested_start >= window_start
                and requested_end <= window_end
            ):
                fits_schedule = True
                break

        if not fits_schedule:
            raise serializers.ValidationError({
                "appointment_time":
                    "The selected appointment does not fit "
                    "within the doctor's available hours."
            })

        # Existing active appointments
        existing = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.CONFIRMED,
            ],
        )

        for appointment in existing:

            existing_start = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time,
            )

            existing_end = (
                existing_start
                + timedelta(
                    minutes=appointment.duration_minutes
                )
            )

            overlaps = (
                existing_start < requested_end
                and existing_end > requested_start
            )

            if overlaps:
                raise serializers.ValidationError({
                    "appointment_time":
                        "The selected time overlaps with "
                        "another appointment."
                })

        return attrs

    def create(self, validated_data):

        doctor = validated_data["doctor"]

        validated_data[
            "duration_minutes"
        ] = doctor.consultation_duration_minutes

        return super().create(
            validated_data
        )
    