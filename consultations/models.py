from django.db import models
from appointments.models import Appointment

class Consultation(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE
    )
    diagnosis = models.TextField()
    notes = models.TextField()
    follow_up_date = models.DateField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Prescription(models.Model):
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE
    )
    medication = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField()

