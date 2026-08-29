from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from patients.models import Patient
from doctors.models import Doctor


class Appointment(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    duration_minutes = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    reason_for_visit = models.TextField()

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cancelled_appointments",
    )

    cancellation_reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-appointment_date",
            "-appointment_time",
        ]

        indexes = [
            models.Index(
                fields=[
                    "doctor",
                    "appointment_date",
                    "appointment_time",
                ]
            ),
            models.Index(
                fields=[
                    "patient",
                    "appointment_date",
                ]
            ),
            models.Index(
                fields=[
                    "status",
                    "appointment_date",
                ]
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(duration_minutes__gt=0),
                name="appointment_duration_positive",
            ),

            models.UniqueConstraint(
                fields=[
                    "doctor",
                    "appointment_date",
                    "appointment_time",
                ],
                condition=Q(
                    status__in=[
                        "pending",
                        "confirmed",
                    ]
                ),
                name="unique_active_doctor_appointment_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.doctor.user.full_name} - "
            f"{self.patient.user.full_name} - "
            f"{self.appointment_date} "
            f"{self.appointment_time}"
        )

    @property
    def end_time(self):
        start = datetime.combine(
            self.appointment_date,
            self.appointment_time,
        )

        return (
            start
            + timedelta(minutes=self.duration_minutes)
        ).time()

    def clean(self):

        errors = {}

        today = timezone.localdate()

        if (
            self.appointment_date
            and self.appointment_date < today
        ):
            errors["appointment_date"] = (
                "Appointment date cannot be in the past."
            )

        if not self.doctor_id:
            errors["doctor"] = "Doctor is required."

        if not self.appointment_time:
            errors["appointment_time"] = (
                "Appointment time is required."
            )

        if errors:
            raise ValidationError(errors)

        weekday = self.appointment_date.strftime(
            "%A"
        ).lower()

        availability = self.doctor.availability.filter(
            day=weekday,
            is_available=True,
        )

        valid_window = False

        appointment_start = datetime.combine(
            self.appointment_date,
            self.appointment_time,
        )

        appointment_end = (
            appointment_start
            + timedelta(
                minutes=self.duration_minutes
            )
        )

        for window in availability:

            window_start = datetime.combine(
                self.appointment_date,
                window.start_time,
            )

            window_end = datetime.combine(
                self.appointment_date,
                window.end_time,
            )

            if (
                appointment_start >= window_start
                and appointment_end <= window_end
            ):
                valid_window = True
                break

        if not valid_window:
            errors["appointment_time"] = (
                "The appointment does not fit within "
                "the doctor's available hours."
            )

        if errors:
            raise ValidationError(errors)

class AppointmentCheckIn(models.Model):

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="check_in",
    )

    checked_in_at = models.DateTimeField()

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    gps_verified = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    