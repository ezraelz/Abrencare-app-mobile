from django.db import models
from accounts.models import User


class Specialty(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField()
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    bio = models.TextField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    specialty = models.ForeignKey(Specialty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Qualification(models.Model):
    doctor = models.ForeignKey(
        "Doctor",
        on_delete=models.CASCADE,
        related_name="qualifications"
    )
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    year_of_completion = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class DoctorAvailability(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
