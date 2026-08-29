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

    otp_sent_at = models.DateTimeField(
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

    otp_locked_at = models.DateTimeField(
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


class FamilyAuditLog(models.Model):
    """
    Immutable audit trail for security-sensitive family operations.

    Never store:
        - raw invitation tokens
        - OTPs
        - passwords
        - authentication tokens
        - unnecessary PHI
    """

    class Action(models.TextChoices):
        FAMILY_CREATED = (
            "family_created",
            "Family Created",
        )

        PATIENT_CREATED = (
            "patient_created",
            "Patient Created",
        )

        MEMBER_INVITED = (
            "member_invited",
            "Family Member Invited",
        )

        PATIENT_CLAIM_INVITED = (
            "patient_claim_invited",
            "Patient Claim Invited",
        )

        INVITATION_OTP_REQUESTED = (
            "invitation_otp_requested",
            "Invitation OTP Requested",
        )

        INVITATION_CONTACT_VERIFIED = (
            "invitation_contact_verified",
            "Invitation Contact Verified",
        )

        MEMBER_ACCEPTED = (
            "member_accepted",
            "Family Membership Accepted",
        )

        MEMBER_REGISTERED = (
            "member_registered",
            "Family Member Registered",
        )

        PATIENT_CLAIMED = (
            "patient_claimed",
            "Patient Account Claimed",
        )

        INVITATION_CANCELLED = (
            "invitation_cancelled",
            "Invitation Cancelled",
        )

        INVITATION_EXPIRED = (
            "invitation_expired",
            "Invitation Expired",
        )

        OTP_LOCKED = (
            "otp_locked",
            "OTP Verification Locked",
        )

    family = models.ForeignKey(
        Family,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_audit_logs",
    )

    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )

    invitation = models.ForeignKey(
        FamilyInvitation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_audit_logs",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["family", "-created_at"],
                name="fa_family_created_idx",
            ),
            models.Index(
                fields=["actor", "-created_at"],
                name="fa_actor_created_idx",
            ),
            models.Index(
                fields=["action", "-created_at"],
                name="fa_action_created_idx",
            ),
            models.Index(
                fields=["invitation", "-created_at"],
                name="fa_inv_created_idx",
            ),
            models.Index(
                fields=["patient", "-created_at"],
                name="fa_patient_created_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.family} - "
            f"{self.action} - "
            f"{self.created_at}"
        )

