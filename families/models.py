import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from patients.models import Patient


class Family(models.Model):
    name = models.CharField(max_length=150)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_families",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return self.name


class FamilyMember(models.Model):

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MEMBER = "member", "Member"
        CAREGIVER = "caregiver", "Caregiver"

    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="family_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    can_view_patient_records = models.BooleanField(default=False)
    can_manage_appointments = models.BooleanField(default=False)
    can_manage_medications = models.BooleanField(default=False)
    can_manage_family_members = models.BooleanField(default=False)
    can_manage_family_patients = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["family", "user"],
                name="unique_family_member",
            ),
            models.UniqueConstraint(
                fields=["family"],
                condition=Q(role="owner"),
                name="unique_family_owner",
            ),
        ]

        indexes = [
            models.Index(fields=["family", "role"]),
            models.Index(fields=["user", "family"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.family}"

      
class FamilyPatient(models.Model):

    class Relationship(models.TextChoices):
        SELF = "self", "Self"
        SPOUSE = "spouse", "Spouse"
        PARENT = "parent", "Parent"
        CHILD = "child", "Child"
        SIBLING = "sibling", "Sibling"
        RELATIVE = "relative", "Relative"
        OTHER = "other", "Other"

    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="patients",
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="family_relationships",
    )

    relationship = models.CharField(
        max_length=30,
        choices=Relationship.choices,
        default=Relationship.OTHER,
    )

    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["family", "patient"],
                name="unique_family_patient",
            ),
            models.UniqueConstraint(
                fields=["family"],
                condition=Q(is_primary=True),
                name="unique_primary_family_patient",
            ),
        ]

        indexes = [
            models.Index(fields=["family", "patient"]),
            models.Index(fields=["patient", "family"]),
        ]

    def __str__(self):
        return f"{self.patient} - {self.family}"

    
class FamilyInvitation(models.Model):

    class InvitationType(models.TextChoices):
        MEMBER = "member", "Family Member"
        PATIENT_CLAIM = "patient_claim", "Patient Account Claim"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="family_invitations_sent",
    )

    invitation_type = models.CharField(
        max_length=30,
        choices=InvitationType.choices,
    )

    name = models.CharField(
        max_length=150,
    )

    email = models.EmailField(
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    role = models.CharField(
        max_length=20,
        choices=FamilyMember.Role.choices,
        blank=True,
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="claim_invitations",
    )

    token_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    expires_at = models.DateTimeField()

    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_family_invitations",
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    otp_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    otp_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    otp_attempts = models.PositiveIntegerField(
        default=0,
    )

    contact_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["email", "status"]),
            models.Index(fields=["phone_number", "status"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.family} - {self.invitation_type}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


class InvitationDelivery(models.Model):

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    invitation = models.ForeignKey(
        FamilyInvitation,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )

    channel = models.CharField(
        max_length=10,
        choices=Channel.choices,
    )

    destination = models.CharField(
        max_length=255,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
