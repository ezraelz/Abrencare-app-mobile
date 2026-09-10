from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, AppointmentCheckIn
from doctors.models import Doctor

# ---------------------------------------------------------------------------
# Shared validation helpers (single source of truth)
# ---------------------------------------------------------------------------

def get_appointment_window(date, time, duration_minutes):
    """Return (start_dt, end_dt) as naive datetimes in local time."""
    start = datetime.combine(date, time)
    end = start + timedelta(minutes=duration_minutes)
    return start, end


def validate_not_in_past(appointment_date, appointment_time=None):
    today = timezone.localdate()
    if appointment_date < today:
        raise serializers.ValidationError(
            {"appointment_date": "Appointment date cannot be in the past."}
        )
    # Optional: block times earlier today
    if appointment_date == today and appointment_time is not None:
        now = timezone.localtime().time()
        if appointment_time < now:
            raise serializers.ValidationError(
                {"appointment_time": "Appointment time cannot be in the past."}
            )


def validate_fits_doctor_availability(doctor, appointment_date, appointment_time, duration_minutes):
    weekday = appointment_date.strftime("%A").lower()
    windows = doctor.availability.filter(day=weekday, is_available=True)

    if not windows.exists():
        raise serializers.ValidationError(
            {"appointment_time": "Doctor has no availability on this day."}
        )

    start, end = get_appointment_window(
        appointment_date, appointment_time, duration_minutes
    )

    for window in windows:
        window_start = datetime.combine(appointment_date, window.start_time)
        window_end = datetime.combine(appointment_date, window.end_time)
        if start >= window_start and end <= window_end:
            return  # fits at least one window

    raise serializers.ValidationError(
        {
            "appointment_time": (
                "The selected appointment does not fit within "
                "the doctor's available hours."
            )
        }
    )


def validate_no_overlap(doctor, appointment_date, appointment_time, duration_minutes, exclude_pk=None):
    """
    Efficient overlap check against active appointments.
    Only loads the minimal set of candidates for the day.
    """
    start, end = get_appointment_window(
        appointment_date, appointment_time, duration_minutes
    )

    qs = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=[
            Appointment.Status.PENDING,
            Appointment.Status.CONFIRMED,
        ],
    ).only("id", "appointment_time", "duration_minutes")

    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    for appt in qs.iterator(chunk_size=50):  # memory-friendly
        existing_start, existing_end = get_appointment_window(
            appointment_date, appt.appointment_time, appt.duration_minutes
        )
        # classic interval overlap
        if existing_start < end and existing_end > start:
            raise serializers.ValidationError(
                {
                    "appointment_time": (
                        "The selected time overlaps with another appointment."
                    )
                }
            )


# ---------------------------------------------------------------------------
# Nested / lightweight serializers
# ---------------------------------------------------------------------------

class AppointmentCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentCheckIn
        fields = [
            "checked_in_at",
            "latitude",
            "longitude",
            "gps_verified",
            "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Main read serializer
# ---------------------------------------------------------------------------

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="patient.user.full_name", read_only=True
    )
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    doctor_name = serializers.CharField(
        source="doctor.user.full_name", read_only=True
    )
    doctor_specialty = serializers.CharField(
        source="doctor.specialty.name", read_only=True, allow_null=True
    )
    cancelled_by_name = serializers.CharField(
        source="cancelled_by.get_full_name", read_only=True, allow_null=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    end_time = serializers.TimeField(read_only=True)
    check_in = AppointmentCheckInSerializer(read_only=True)
    is_upcoming = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_confirm = serializers.SerializerMethodField()
    can_complete = serializers.SerializerMethodField()
    can_mark_no_show = serializers.SerializerMethodField()

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
            "status_display",
            "reason_for_visit",
            "confirmed_at",
            "completed_at",
            "cancelled_at",
            "cancelled_by",
            "cancelled_by_name",
            "cancellation_reason",
            "check_in",
            "is_upcoming",
            "can_cancel",
            "can_confirm",
            "can_complete",
            "can_mark_no_show",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields  # fully read-only

    def get_is_upcoming(self, obj):
        today = timezone.localdate()
        if obj.appointment_date > today:
            return True
        if obj.appointment_date == today:
            return obj.appointment_time >= timezone.localtime().time()
        return False

    def _user_is_doctor_of(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return (
            hasattr(request.user, "doctor_profile")
            and obj.doctor.user_id == request.user.id
        )

    def _user_is_patient_of(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return (
            hasattr(request.user, "patient_profile")
            and obj.patient.user_id == request.user.id
        )

    def get_can_cancel(self, obj):
        if obj.status in (
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
            Appointment.Status.NO_SHOW,
        ):
            return False
        request = self.context.get("request")
        if not request:
            return False
        return (
            request.user.is_staff
            or self._user_is_doctor_of(obj)
            or self._user_is_patient_of(obj)
        )

    def get_can_confirm(self, obj):
        if obj.status != Appointment.Status.PENDING:
            return False
        request = self.context.get("request")
        return bool(
            request
            and (request.user.is_staff or self._user_is_doctor_of(obj))
        )

    def get_can_complete(self, obj):
        if obj.status != Appointment.Status.CONFIRMED:
            return False
        request = self.context.get("request")
        return bool(
            request
            and (request.user.is_staff or self._user_is_doctor_of(obj))
        )

    def get_can_mark_no_show(self, obj):
        return self.get_can_complete(obj)


# ---------------------------------------------------------------------------
# Create serializer
# ---------------------------------------------------------------------------

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "doctor",
            "appointment_date",
            "appointment_time",
            #"reason_for_visit",
        ]

    def validate(self, attrs):
        doctor = attrs["doctor"]
        appointment_date = attrs["appointment_date"]
        appointment_time = attrs["appointment_time"]

        # Duration comes exclusively from the doctor
        duration = getattr(doctor, "consultation_duration_minutes", None)
        if not duration or duration <= 0:
            raise serializers.ValidationError(
                {
                    "doctor": (
                        "Doctor does not have a valid consultation duration configured."
                    )
                }
            )

        validate_not_in_past(appointment_date, appointment_time)
        validate_fits_doctor_availability(
            doctor, appointment_date, appointment_time, duration
        )
        validate_no_overlap(
            doctor, appointment_date, appointment_time, duration
        )

        # Stash duration so create() can use it without another lookup
        attrs["_duration_minutes"] = duration
        return attrs

    def create(self, validated_data):
        duration = validated_data.pop("_duration_minutes")
        validated_data["duration_minutes"] = duration
        # patient and status are injected by the view
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Optional action-specific input serializers (recommended for production)
# ---------------------------------------------------------------------------

class AppointmentCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        default="",
    )


class AppointmentRescheduleSerializer(serializers.Serializer):
    """
    Lightweight input for a future reschedule endpoint.
    Reuses the same validation helpers.
    """
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()
    reason_for_visit = serializers.CharField(
        required=False, allow_blank=True, max_length=2000
    )

    def validate(self, attrs):
        appointment = self.context["appointment"]
        doctor = appointment.doctor
        duration = appointment.duration_minutes

        validate_not_in_past(attrs["appointment_date"], attrs["appointment_time"])
        validate_fits_doctor_availability(
            doctor,
            attrs["appointment_date"],
            attrs["appointment_time"],
            duration,
        )
        validate_no_overlap(
            doctor,
            attrs["appointment_date"],
            attrs["appointment_time"],
            duration,
            exclude_pk=appointment.pk,
        )
        return attrs