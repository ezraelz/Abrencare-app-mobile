from django.db import models
from patients.models import Patient
from doctors.models import Doctor

class Appointment(models.Model):

    STATUS = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Scheduling(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

