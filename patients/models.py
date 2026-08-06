from django.db import models
from accounts.models import User
from doctors.models import Doctor


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=5)
    emergency_contact = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.user.username
    
class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True
    )
    diagnosis = models.TextField()
    treatment = models.TextField()
    allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class MedicalDocument(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="medical_documents/")
    description = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

