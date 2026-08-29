import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from patients.models import Patient

from .models import (
    Family,
    FamilyMember,
    FamilyPatient,
    FamilyInvitation,
    InvitationDelivery,
)

User = get_user_model()


INVITATION_EXPIRY_DAYS = 7
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


# ============================================================
# TOKEN HELPERS
# ============================================================

def generate_invitation_token():
    """
    Generate a cryptographically secure invitation token.

    Only the hash is persisted in the database.
    The raw token must only be available to the delivery layer.
    """

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    return raw_token, token_hash


def hash_invitation_token(token):
    """
    Hash an invitation token for database lookup.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# ============================================================
# OTP HELPERS
# ============================================================

def generate_otp():
    """
    Generate a six-digit cryptographically secure OTP.
    """

    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp):
    """
    Hash an OTP before persistence.
    """

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


# ============================================================
# FAMILY
# ============================================================

@transaction.atomic
def create_family(*, user, name):
    family = Family.objects.create(
        name=name,
        created_by=user,
    )

    FamilyMember.objects.create(
        family=family,
        user=user,
        role=FamilyMember.Role.OWNER,
        can_view_patient_records=True,
        can_manage_appointments=True,
        can_manage_medications=True,
        can_manage_family_members=True,
        can_manage_family_patients=True,
    )

    return family


# ============================================================
# CREATE FAMILY PATIENT
# ============================================================

@transaction.atomic
def create_family_patient(
    *,
    family,
    created_by,
    validated_data,
):
    """
    Create a patient and associate them with a family.

    Existing users are reused by email or phone.

    New patient accounts are created as pending users with
    unusable passwords.
    """

    email = validated_data.get("email")
    phone = validated_data.get("phone_number")

    user = None

    # --------------------------------------------------------
    # Find existing user
    # --------------------------------------------------------

    if email:
        user = User.objects.filter(
            email__iexact=email
        ).first()

    if not user and phone:
        user = User.objects.filter(
            phone_number=phone
        ).first()

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    if not user:
        username = (
            validated_data.get("username")
            or secrets.token_hex(8)
        )

        user = User(
            username=username,
            email=email or None,
            phone_number=phone or None,
            first_name=validated_data["first_name"],
            last_name=validated_data.get(
                "last_name",
                "",
            ),
            date_of_birth=validated_data.get(
                "date_of_birth"
            ),
            account_status="pending",
        )

        user.set_unusable_password()
        user.save()

    # --------------------------------------------------------
    # Existing patient profile
    # --------------------------------------------------------

    patient = getattr(
        user,
        "patient_profile",
        None,
    )

    if not patient:
        patient = Patient.objects.create(
            user=user,
            gender=validated_data.get(
                "gender",
                "",
            ),
            blood_group=validated_data.get(
                "blood_group",
                "",
            ),
        )

    # --------------------------------------------------------
    # Prevent duplicate family relationship
    # --------------------------------------------------------

    family_patient, created = (
        FamilyPatient.objects.get_or_create(
            family=family,
            patient=patient,
            defaults={
                "relationship": validated_data.get(
                    "relationship",
                    FamilyPatient.Relationship.OTHER,
                ),
                "is_primary": validated_data.get(
                    "is_primary",
                    False,
                ),
            },
        )
    )

    if not created:
        raise ValueError(
            "This patient already belongs to the family."
        )

    return family_patient


# ============================================================
# INVITE FAMILY MEMBER
# ============================================================

@transaction.atomic
def invite_family_member(
    *,
    family,
    invited_by,
    validated_data,
):
    """
    Create a family-member invitation.

    A User is NOT created here.

    The invitation recipient can either:
        - accept as an existing authenticated user
        - complete registration as a new user
    """

    email = validated_data.get("email")
    phone = validated_data.get("phone_number")

    existing_user = None

    # --------------------------------------------------------
    # Find existing account
    # --------------------------------------------------------

    if email:
        existing_user = User.objects.filter(
            email__iexact=email
        ).first()

    if not existing_user and phone:
        existing_user = User.objects.filter(
            phone_number=phone
        ).first()

    # --------------------------------------------------------
    # Prevent duplicate membership
    # --------------------------------------------------------

    if existing_user:
        if FamilyMember.objects.filter(
            family=family,
            user=existing_user,
        ).exists():
            raise ValueError(
                "This user is already a member of the family."
            )

    # --------------------------------------------------------
    # Cancel previous pending invitation
    # --------------------------------------------------------

    pending_filter = {
        "family": family,
        "invitation_type": (
            FamilyInvitation.InvitationType.MEMBER
        ),
        "status": FamilyInvitation.Status.PENDING,
    }

    if email:
        pending_filter["email__iexact"] = email
    elif phone:
        pending_filter["phone_number"] = phone

    FamilyInvitation.objects.filter(
        **pending_filter
    ).update(
        status=FamilyInvitation.Status.CANCELLED
    )

    # --------------------------------------------------------
    # Generate token
    # --------------------------------------------------------

    raw_token, token_hash = generate_invitation_token()

    invitation = FamilyInvitation.objects.create(
        family=family,
        invited_by=invited_by,
        invitation_type=(
            FamilyInvitation.InvitationType.MEMBER
        ),
        name=validated_data["name"],
        email=email or "",
        phone_number=phone or "",
        role=validated_data.get(
            "role",
            FamilyMember.Role.MEMBER,
        ),
        token_hash=token_hash,
        expires_at=(
            timezone.now()
            + timedelta(days=INVITATION_EXPIRY_DAYS)
        ),
    )

    return invitation, raw_token


# ============================================================
# PATIENT CLAIM INVITATION
# ============================================================

@transaction.atomic
def create_patient_claim_invitation(
    *,
    family,
    patient,
    invited_by,
    validated_data,
):
    """
    Create an invitation allowing a pending patient
    to claim their existing patient account.
    """

    if not patient:
        raise ValueError(
            "Patient is required."
        )

    user = patient.user

    if user.account_status == "active":
        raise ValueError(
            "This patient already has an active account."
        )

    email = validated_data.get("email")
    phone = validated_data.get("phone_number")

    if not email and not phone:
        raise ValueError(
            "Email or phone number is required."
        )

    # --------------------------------------------------------
    # Cancel previous claim invitations
    # --------------------------------------------------------

    FamilyInvitation.objects.filter(
        patient=patient,
        invitation_type=(
            FamilyInvitation.InvitationType.PATIENT_CLAIM
        ),
        status=FamilyInvitation.Status.PENDING,
    ).update(
        status=FamilyInvitation.Status.CANCELLED
    )

    # --------------------------------------------------------
    # Generate token
    # --------------------------------------------------------

    raw_token, token_hash = generate_invitation_token()

    invitation = FamilyInvitation.objects.create(
        family=family,
        invited_by=invited_by,
        invitation_type=(
            FamilyInvitation.InvitationType.PATIENT_CLAIM
        ),
        name=user.full_name,
        email=email or "",
        phone_number=phone or "",
        patient=patient,
        token_hash=token_hash,
        expires_at=(
            timezone.now()
            + timedelta(days=INVITATION_EXPIRY_DAYS)
        ),
    )

    return invitation, raw_token


# ============================================================
# INVITATION LOOKUP
# ============================================================

def get_invitation_by_token(token):
    """
    Resolve an invitation from a raw token.

    Security-sensitive validation belongs here rather than
    inside the views.
    """

    if not token:
        raise ValueError(
            "Invitation token is required."
        )

    token_hash = hash_invitation_token(token)

    invitation = (
        FamilyInvitation.objects
        .select_related(
            "family",
            "invited_by",
            "patient",
            "patient__user",
        )
        .filter(
            token_hash=token_hash,
        )
        .first()
    )

    if not invitation:
        raise ValueError(
            "Invalid invitation."
        )

    # --------------------------------------------------------
    # Expiration
    # --------------------------------------------------------

    if invitation.expires_at <= timezone.now():
        if invitation.status == FamilyInvitation.Status.PENDING:
            invitation.status = (
                FamilyInvitation.Status.EXPIRED
            )
            invitation.save(
                update_fields=["status"]
            )

        raise ValueError(
            "This invitation has expired."
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if invitation.status != FamilyInvitation.Status.PENDING:
        raise ValueError(
            "This invitation is no longer active."
        )

    return invitation


# ============================================================
# CONTACT VERIFICATION
# ============================================================

@transaction.atomic
def request_invitation_contact_verification(*, token):
    """
    Generate and prepare an OTP for invitation verification.

    The OTP itself must never be returned to the API client.

    The notification layer should receive the raw OTP.
    """

    invitation = get_invitation_by_token(token)

    # --------------------------------------------------------
    # Prevent verification after acceptance
    # --------------------------------------------------------

    if invitation.status != FamilyInvitation.Status.PENDING:
        raise ValueError(
            "This invitation is no longer active."
        )

    # --------------------------------------------------------
    # Validate contact
    # --------------------------------------------------------

    if invitation.email:
        channel = "email"
        destination = invitation.email

    elif invitation.phone_number:
        channel = "sms"
        destination = invitation.phone_number

    else:
        raise ValueError(
            "This invitation has no contact information."
        )

    # --------------------------------------------------------
    # Generate OTP
    # --------------------------------------------------------

    otp = generate_otp()
    otp_hash = hash_otp(otp)

    invitation.otp_hash = otp_hash
    invitation.otp_expires_at = (
        timezone.now()
        + timedelta(minutes=OTP_EXPIRY_MINUTES)
    )
    invitation.otp_attempts = 0

    invitation.save(
        update_fields=[
            "otp_hash",
            "otp_expires_at",
            "otp_attempts",
        ]
    )

    # --------------------------------------------------------
    # Record delivery
    # --------------------------------------------------------

    delivery = InvitationDelivery.objects.create(
        invitation=invitation,
        channel=channel,
        destination=destination,
        status=InvitationDelivery.Status.PENDING,
    )

    # --------------------------------------------------------
    # Notification layer
    # --------------------------------------------------------
    #
    # The raw OTP exists only in memory.
    #
    # Example:
    #
    # send_invitation_otp(
    #     invitation=invitation,
    #     otp=otp,
    #     channel=channel,
    #     destination=destination,
    # )
    #
    # The actual email/SMS integration should live outside
    # this service.
    #
    # --------------------------------------------------------

    return {
        "channel": channel,
        "destination": _mask_contact(
            destination,
            channel,
        ),
        "expires_in": OTP_EXPIRY_MINUTES * 60,
        "delivery_id": delivery.id,
        "otp": otp,  # REMOVE from production API response
    }


def _mask_contact(value, channel):
    """
    Mask an email address or phone number before exposing
    it to the frontend.
    """

    if not value:
        return ""

    if channel == "email":
        local, domain = value.split(
            "@",
            1,
        )

        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = (
                local[0]
                + "*" * (len(local) - 2)
                + local[-1]
            )

        return f"{masked_local}@{domain}"

    # phone
    if len(value) <= 4:
        return "*" * len(value)

    return (
        "*" * (len(value) - 4)
        + value[-4:]
    )


# ============================================================
# VERIFY OTP
# ============================================================

@transaction.atomic
def verify_invitation_otp(*, token, otp):
    """
    Verify the invitation OTP.

    Successful verification marks the invitation contact
    as verified.

    It does NOT accept the invitation.
    """

    invitation = get_invitation_by_token(token)

    if not invitation.otp_hash:
        raise ValueError(
            "No verification code has been requested."
        )

    if (
        not invitation.otp_expires_at
        or invitation.otp_expires_at <= timezone.now()
    ):
        raise ValueError(
            "The verification code has expired."
        )

    if invitation.otp_attempts >= OTP_MAX_ATTEMPTS:
        raise ValueError(
            "Too many verification attempts. "
            "Please request a new code."
        )

    # --------------------------------------------------------
    # Increment attempt counter
    # --------------------------------------------------------

    invitation.otp_attempts += 1

    # --------------------------------------------------------
    # Verify OTP
    # --------------------------------------------------------

    if hash_otp(otp) != invitation.otp_hash:
        invitation.save(
            update_fields=["otp_attempts"]
        )

        remaining = max(
            OTP_MAX_ATTEMPTS
            - invitation.otp_attempts,
            0,
        )

        raise ValueError(
            f"Invalid verification code. "
            f"{remaining} attempts remaining."
        )

    # --------------------------------------------------------
    # Successful verification
    # --------------------------------------------------------

    now = timezone.now()

    invitation.contact_verified_at = now

    invitation.otp_hash = ""
    invitation.otp_expires_at = None
    invitation.otp_attempts = 0

    invitation.save(
        update_fields=[
            "contact_verified_at",
            "otp_hash",
            "otp_expires_at",
            "otp_attempts",
        ]
    )

    return {
        "verified": True,
        "verified_at": now,
    }


# ============================================================
# VERIFICATION HELPER
# ============================================================

def _require_verified_invitation(invitation):
    """
    Ensure the recipient has completed contact verification.
    """

    if not invitation.contact_verified_at:
        raise ValueError(
            "Contact verification is required before "
            "accepting this invitation."
        )


# ============================================================
# ACCEPT INVITATION — EXISTING USER
# ============================================================

@transaction.atomic
def accept_invitation(*, token, user):
    """
    Accept a family-member invitation for an existing user.

    Requirements:

        - valid invitation
        - MEMBER invitation
        - verified contact
        - authenticated user
        - contact belongs to authenticated user
        - user is not already a family member

    The invitation is consumed atomically.
    """

    invitation = (
        get_invitation_by_token(token)
    )

    # --------------------------------------------------------
    # Invitation type
    # --------------------------------------------------------

    if invitation.invitation_type != (
        FamilyInvitation.InvitationType.MEMBER
    ):
        raise ValueError(
            "This invitation cannot be accepted as a "
            "family-member invitation."
        )

    # --------------------------------------------------------
    # Contact verification
    # --------------------------------------------------------

    _require_verified_invitation(
        invitation
    )

    # --------------------------------------------------------
    # Ensure invitation belongs to user
    # --------------------------------------------------------

    email_matches = (
        invitation.email
        and user.email
        and invitation.email.lower()
        == user.email.lower()
    )

    phone_matches = (
        invitation.phone_number
        and user.phone_number
        and invitation.phone_number
        == user.phone_number
    )

    if not email_matches and not phone_matches:
        raise ValueError(
            "This invitation was not issued for "
            "the authenticated user's contact information."
        )

    # --------------------------------------------------------
    # Prevent duplicate membership
    # --------------------------------------------------------

    if FamilyMember.objects.filter(
        family=invitation.family,
        user=user,
    ).exists():
        raise ValueError(
            "You are already a member of this family."
        )

    # --------------------------------------------------------
    # Create membership
    # --------------------------------------------------------

    member = FamilyMember.objects.create(
        family=invitation.family,
        user=user,
        role=invitation.role,
    )

    # --------------------------------------------------------
    # Consume invitation
    # --------------------------------------------------------

    invitation.status = (
        FamilyInvitation.Status.ACCEPTED
    )

    invitation.accepted_at = timezone.now()

    invitation.save(
        update_fields=[
            "status",
            "accepted_at",
        ]
    )

    return member


# ============================================================
# COMPLETE INVITATION REGISTRATION
# ============================================================

@transaction.atomic
def complete_invitation_registration(
    *,
    token,
    validated_data,
):
    """
    Complete registration for a new family member.

    This creates the User only after the invitation's
    contact has been verified.

    The invitation itself becomes consumed atomically.
    """

    invitation = (
        get_invitation_by_token(token)
    )

    # --------------------------------------------------------
    # Type
    # --------------------------------------------------------

    if invitation.invitation_type != (
        FamilyInvitation.InvitationType.MEMBER
    ):
        raise ValueError(
            "This invitation is not a family-member invitation."
        )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    _require_verified_invitation(
        invitation
    )

    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    password = validated_data.get(
        "password"
    )

    if not password:
        raise ValueError(
            "Password is required."
        )

    # --------------------------------------------------------
    # Determine contact
    # --------------------------------------------------------

    email = invitation.email or None
    phone = invitation.phone_number or None

    # --------------------------------------------------------
    # Prevent account collision
    # --------------------------------------------------------

    if email:
        existing_user = User.objects.filter(
            email__iexact=email
        ).first()

        if existing_user:
            raise ValueError(
                "An account already exists for this email. "
                "Please sign in and accept the invitation."
            )

    if phone:
        existing_user = User.objects.filter(
            phone_number=phone
        ).first()

        if existing_user:
            raise ValueError(
                "An account already exists for this phone "
                "number. Please sign in and accept the invitation."
            )

    # --------------------------------------------------------
    # Username
    # --------------------------------------------------------

    username = (
        validated_data.get("username")
        or secrets.token_hex(8)
    )

    if User.objects.filter(
        username=username
    ).exists():
        raise ValueError(
            "This username is already in use."
        )

    # --------------------------------------------------------
    # Create account
    # --------------------------------------------------------

    user = User(
        username=username,
        email=email,
        phone_number=phone,
        first_name=validated_data.get(
            "first_name",
            invitation.name.split(" ")[0]
            if invitation.name
            else "",
        ),
        last_name=validated_data.get(
            "last_name",
            "",
        ),
        account_status="active",
    )

    user.set_password(password)
    user.save()

    # --------------------------------------------------------
    # Create family membership
    # --------------------------------------------------------

    member = FamilyMember.objects.create(
        family=invitation.family,
        user=user,
        role=invitation.role,
    )

    # --------------------------------------------------------
    # Consume invitation
    # --------------------------------------------------------

    invitation.status = (
        FamilyInvitation.Status.ACCEPTED
    )
    invitation.accepted_at = timezone.now()

    invitation.save(
        update_fields=[
            "status",
            "accepted_at",
        ]
    )

    return user, member


# ============================================================
# COMPLETE PATIENT CLAIM
# ============================================================

@transaction.atomic
def complete_patient_claim(
    *,
    token,
    validated_data,
):
    """
    Complete a patient account claim.

    IMPORTANT:

    This does NOT create a new Patient.

    The existing:
        User
        Patient
        FamilyPatient

    records are retained.

    The pending User is activated and receives a password.
    """

    invitation = (
        get_invitation_by_token(token)
    )

    # --------------------------------------------------------
    # Invitation type
    # --------------------------------------------------------

    if invitation.invitation_type != (
        FamilyInvitation.InvitationType.PATIENT_CLAIM
    ):
        raise ValueError(
            "This invitation is not a patient claim invitation."
        )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    _require_verified_invitation(
        invitation
    )

    # --------------------------------------------------------
    # Patient
    # --------------------------------------------------------

    patient = invitation.patient

    if not patient:
        raise ValueError(
            "This patient claim invitation is not linked "
            "to a patient."
        )

    user = patient.user

    if not user:
        raise ValueError(
            "The patient does not have an associated user account."
        )

    # --------------------------------------------------------
    # Account state
    # --------------------------------------------------------

    if user.account_status == "active":
        raise ValueError(
            "This patient account is already active."
        )

    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    password = validated_data.get(
        "password"
    )

    if not password:
        raise ValueError(
            "Password is required."
        )

    # --------------------------------------------------------
    # Username
    # --------------------------------------------------------

    username = validated_data.get(
        "username"
    )

    if username:
        existing_username_user = (
            User.objects
            .filter(username=username)
            .exclude(pk=user.pk)
            .first()
        )

        if existing_username_user:
            raise ValueError(
                "This username is already in use."
            )

        user.username = username

    # --------------------------------------------------------
    # Update verified contact
    # --------------------------------------------------------

    if invitation.email:
        existing_email_user = (
            User.objects
            .filter(
                email__iexact=invitation.email
            )
            .exclude(pk=user.pk)
            .first()
        )

        if existing_email_user:
            raise ValueError(
                "This email is already associated "
                "with another account."
            )

        user.email = invitation.email

    if invitation.phone_number:
        existing_phone_user = (
            User.objects
            .filter(
                phone_number=invitation.phone_number
            )
            .exclude(pk=user.pk)
            .first()
        )

        if existing_phone_user:
            raise ValueError(
                "This phone number is already associated "
                "with another account."
            )

        user.phone_number = invitation.phone_number

    # --------------------------------------------------------
    # Optional profile data
    # --------------------------------------------------------

    if validated_data.get("first_name"):
        user.first_name = validated_data["first_name"]

    if validated_data.get("last_name"):
        user.last_name = validated_data["last_name"]

    # --------------------------------------------------------
    # Activate account
    # --------------------------------------------------------

    user.account_status = "active"
    user.set_password(password)

    user.save()

    # --------------------------------------------------------
    # Consume invitation
    # --------------------------------------------------------

    invitation.status = (
        FamilyInvitation.Status.ACCEPTED
    )
    invitation.accepted_at = timezone.now()

    invitation.save(
        update_fields=[
            "status",
            "accepted_at",
        ]
    )

    return user, patient
