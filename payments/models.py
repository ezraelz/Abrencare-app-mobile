from django.db import models
from appointments.models import Appointment

class Payment(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=200)
    paid_at = models.DateTimeField(null=True)

