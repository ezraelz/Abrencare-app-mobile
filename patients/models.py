from django.db import models
from accounts.models import User
from doctors.models import Doctor

class Patient(models.Model):

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = (
            "prefer_not_to_say",
            "Prefer not to say",
        )

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"
        UNKNOWN = "unknown", "Unknown"

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="patient_profile",
    )

    gender = models.CharField(
        max_length=30,
        choices=Gender.choices,
        null=True,
        blank=True,
    )

    blood_group = models.CharField(
        max_length=10,
        choices=BloodGroup.choices,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.full_name or self.user.username

class EmergencyContact(models.Model):

    class Relationship(models.TextChoices):
        PARENT = "parent", "Parent"
        SPOUSE = "spouse", "Spouse"
        SIBLING = "sibling", "Sibling"
        CHILD = "child", "Child"
        RELATIVE = "relative", "Relative"
        FRIEND = "friend", "Friend"
        OTHER = "other", "Other"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )

    name = models.CharField(
        max_length=150,
    )

    relationship = models.CharField(
        max_length=30,
        choices=Relationship.choices,
    )

    phone_number = models.CharField(
        max_length=20,
    )

    alternative_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-is_primary", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient"],
                condition=models.Q(is_primary=True),
                name="unique_primary_emergency_contact",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.patient}"
    
class MedicalRecord(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="medical_records",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_records",
    )

    diagnosis = models.TextField()

    treatment = models.TextField(
        blank=True,
    )

    allergies = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Medical record - "
            f"{self.patient}"
        )

class MedicalDocument(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="medical_documents",
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="uploaded_medical_documents",
    )

    file = models.FileField(
        upload_to="medical_documents/%Y/%m/"
    )

    description = models.CharField(
        max_length=255
    )

    version = models.PositiveIntegerField(
        default=1
    )

    is_current = models.BooleanField(
        default=True
    )

    replaced_document = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replacement",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-uploaded_at"]

        indexes = [
            models.Index(
                fields=["patient", "-uploaded_at"]
            ),
            models.Index(
                fields=["patient", "is_current"]
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["replaced_document"],
                condition=models.Q(
                    replaced_document__isnull=False
                ),
                name="unique_document_replacement",
            ),
        ]

    def __str__(self):
        return (
            f"{self.patient.user.full_name} - "
            f"{self.description} - "
            f"v{self.version}"
        )

