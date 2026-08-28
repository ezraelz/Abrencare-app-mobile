from django.db import models
from accounts.models import User


class Specialty(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name


class Doctor(models.Model):

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="doctor",
    )

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="doctors",
    )

    license_number = models.CharField(
        max_length=100,
        unique=True,
    )

    years_of_experience = models.PositiveIntegerField(
        default=0,
    )

    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    consultation_duration = models.PositiveIntegerField(
        default=30,
        help_text="Default consultation duration in minutes.",
    )

    bio = models.TextField(
        blank=True,
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_doctors",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "user__first_name",
            "user__last_name",
        ]

    def __str__(self):
        return (
            self.user.full_name
            or self.user.username
        )
    

class Qualification(models.Model):

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="qualifications",
    )

    degree = models.CharField(
        max_length=150,
    )

    institution = models.CharField(
        max_length=200,
    )

    year_of_completion = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-year_of_completion",
        ]

    def __str__(self):
        return f"{self.degree} - {self.institution}"

class DoctorAvailability(models.Model):

    class Day(models.TextChoices):
        MONDAY = "monday", "Monday"
        TUESDAY = "tuesday", "Tuesday"
        WEDNESDAY = "wednesday", "Wednesday"
        THURSDAY = "thursday", "Thursday"
        FRIDAY = "friday", "Friday"
        SATURDAY = "saturday", "Saturday"
        SUNDAY = "sunday", "Sunday"

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="availability",
    )

    day = models.CharField(
        max_length=10,
        choices=Day.choices,
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_available = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "day",
            "start_time",
        ]

        indexes = [
            models.Index(
                fields=[
                    "doctor",
                    "day",
                    "is_available",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.doctor} - "
            f"{self.day} "
            f"{self.start_time} - "
            f"{self.end_time}"
        )
