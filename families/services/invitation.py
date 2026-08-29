import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.db import transaction
from django.utils import timezone

from ..models import (
    Family,
    FamilyMember,
    FamilyPatient,
    FamilyInvitation,
    FamilyAuditLog,
)

from .audit import create_audit_log


User = get_user_model()


INVITATION_EXPIRY_DAYS = 7


# ============================================================
# TOKEN HELPERS
# ============================================================

def generate_invitation_token():
    """
    Generate a secure invitation token.

    Only the hash is persisted.
    """

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    return raw_token, token_hash


def hash_invitation_token(token):
    """
    Hash a raw invitation token.
    """

    if not token:
        return ""

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# ============================================================
# INVITATION LOOKUP
# ============================================================

def _get_invitation(
    token,
    *,
    for_update=False,
):
    """
    Resolve an invitation from its raw token.

    When for_update=True the invitation is locked
    for the surrounding transaction.
    """

    if not token:
        raise ValueError(
            "Invitation token is required."
        )

    token_hash = hash_invitation_token(token)

    queryset = (
        FamilyInvitation.objects
        .select_related(
            "family",
            "invited_by",
            "accepted_by",
            "patient",
            "patient__user",
        )
    )

    if for_update:
        queryset = queryset.select_for_update()

    invitation = (
        queryset
        .filter(token_hash=token_hash)
        .first()
    )

    if not invitation:
        raise ValueError(
            "Invalid invitation."
        )

    now = timezone.now()

    # --------------------------------------------------------
    # Expiration
    # --------------------------------------------------------

    if invitation.expires_at <= now:

        if invitation.status == (
            FamilyInvitation.Status.PENDING
        ):
            invitation.status = (
                FamilyInvitation.Status.EXPIRED
            )

            invitation.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            create_audit_log(
                family=invitation.family,
                action=FamilyAuditLog.Action.INVITATION_EXPIRED,
                invitation=invitation,
                patient=invitation.patient,
            )

        raise ValueError(
            "This invitation has expired."
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if invitation.status != (
        FamilyInvitation.Status.PENDING
    ):
        raise ValueError(
            "This invitation is no longer active."
        )

    return invitation


def get_invitation_by_token(token):
    """
    Public invitation lookup without row locking.
    """

    return _get_invitation(
        token,
        for_update=False,
    )


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

    Returns:

        invitation, raw_token

    The raw token must only be passed to the notification
    layer and must never be persisted or logged.
    """

    email = (
        validated_data.get("email")
        or ""
    ).strip().lower()

    phone = (
        validated_data.get("phone_number")
        or ""
    ).strip()

    existing_user = None

    # --------------------------------------------------------
    # Existing account
    # --------------------------------------------------------

    if email:
        existing_user = (
            User.objects
            .filter(email__iexact=email)
            .first()
        )

    if not existing_user and phone:
        existing_user = (
            User.objects
            .filter(phone_number=phone)
            .first()
        )

    # --------------------------------------------------------
    # Existing membership
    # --------------------------------------------------------

    if existing_user:

        if FamilyMember.objects.filter(
            family=family,
            user=existing_user,
        ).exists():
            raise ValueError(
                "This user is already a member "
                "of the family."
            )

    # --------------------------------------------------------
    # Cancel previous pending invitation
    # --------------------------------------------------------

    pending_filter = {
        "family": family,
        "invitation_type": (
            FamilyInvitation
            .InvitationType
            .MEMBER
        ),
        "status": (
            FamilyInvitation
            .Status
            .PENDING
        ),
    }

    if email:
        pending_filter["email__iexact"] = email

    elif phone:
        pending_filter["phone_number"] = phone

    cancelled_count = (
        FamilyInvitation.objects
        .filter(**pending_filter)
        .update(
            status=(
                FamilyInvitation
                .Status
                .CANCELLED
            )
        )
    )

    # --------------------------------------------------------
    # Generate token
    # --------------------------------------------------------

    raw_token, token_hash = (
        generate_invitation_token()
    )

    invitation = FamilyInvitation.objects.create(
        family=family,
        invited_by=invited_by,
        invitation_type=(
            FamilyInvitation
            .InvitationType
            .MEMBER
        ),
        name=validated_data["name"],
        email=email,
        phone_number=phone,
        role=validated_data.get(
            "role",
            FamilyMember.Role.MEMBER,
        ),
        token_hash=token_hash,
        expires_at=(
            timezone.now()
            + timedelta(
                days=INVITATION_EXPIRY_DAYS
            )
        ),
    )

    create_audit_log(
        family=family,
        actor=invited_by,
        action=FamilyAuditLog.Action.MEMBER_INVITED,
        invitation=invitation,
        metadata={
            "role": invitation.role,
            "cancelled_previous_invitations": (
                cancelled_count
            ),
        },
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
    Create an invitation for a pending patient
    to claim their existing patient account.
    """

    if not patient:
        raise ValueError(
            "Patient is required."
        )

    user = getattr(
        patient,
        "user",
        None,
    )

    if not user:
        raise ValueError(
            "The patient does not have "
            "an associated user account."
        )

    if user.account_status == "active":
        raise ValueError(
            "This patient already has "
            "an active account."
        )

    email = (
        validated_data.get("email")
        or ""
    ).strip().lower()

    phone = (
        validated_data.get("phone_number")
        or ""
    ).strip()

    if not email and not phone:
        raise ValueError(
            "Email or phone number is required."
        )

    # --------------------------------------------------------
    # Verify contact against patient
    # --------------------------------------------------------

    if email:
        if (
            user.email
            and user.email.lower() != email
        ):
            raise ValueError(
                "The email does not match "
                "the patient's account."
            )

    if phone:
        if (
            user.phone_number
            and user.phone_number != phone
        ):
            raise ValueError(
                "The phone number does not match "
                "the patient's account."
            )

    # --------------------------------------------------------
    # Cancel previous claim invitations
    # --------------------------------------------------------

    cancelled_count = (
        FamilyInvitation.objects
        .filter(
            patient=patient,
            invitation_type=(
                FamilyInvitation
                .InvitationType
                .PATIENT_CLAIM
            ),
            status=(
                FamilyInvitation
                .Status
                .PENDING
            ),
        )
        .update(
            status=(
                FamilyInvitation
                .Status
                .CANCELLED
            )
        )
    )

    # --------------------------------------------------------
    # Generate token
    # --------------------------------------------------------

    raw_token, token_hash = (
        generate_invitation_token()
    )

    invitation = FamilyInvitation.objects.create(
        family=family,
        invited_by=invited_by,
        invitation_type=(
            FamilyInvitation
            .InvitationType
            .PATIENT_CLAIM
        ),
        name=user.full_name,
        email=email,
        phone_number=phone,
        patient=patient,
        token_hash=token_hash,
        expires_at=(
            timezone.now()
            + timedelta(
                days=INVITATION_EXPIRY_DAYS
            )
        ),
    )

    create_audit_log(
        family=family,
        actor=invited_by,
        action=(
            FamilyAuditLog.Action
            .PATIENT_CLAIM_INVITED
        ),
        invitation=invitation,
        patient=patient,
        metadata={
            "cancelled_previous_invitations": (
                cancelled_count
            ),
        },
    )

    return invitation, raw_token


# ============================================================
# CONTACT OWNERSHIP
# ============================================================

def invitation_belongs_to_user(
    *,
    invitation,
    user,
):
    """
    Verify that the invitation contact matches
    the authenticated user's verified contact.
    """

    invitation_email = (
        invitation.email or ""
    ).strip().lower()

    user_email = (
        getattr(user, "email", "")
        or ""
    ).strip().lower()

    invitation_phone = (
        invitation.phone_number or ""
    ).strip()

    user_phone = (
        getattr(user, "phone_number", "")
        or ""
    ).strip()

    email_matches = bool(
        invitation_email
        and user_email
        and invitation_email == user_email
    )

    phone_matches = bool(
        invitation_phone
        and user_phone
        and invitation_phone == user_phone
    )

    return email_matches or phone_matches


def require_verified_invitation(
    invitation,
):
    """
    Ensure contact verification occurred.
    """

    if not invitation.contact_verified_at:
        raise ValueError(
            "Contact verification is required "
            "before completing this invitation."
        )


# ============================================================
# ACCEPT INVITATION — EXISTING USER
# ============================================================

@transaction.atomic
def accept_invitation(
    *,
    token,
    user,
):
    """
    Accept a MEMBER invitation for an existing user.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    if invitation.invitation_type != (
        FamilyInvitation
        .InvitationType
        .MEMBER
    ):
        raise ValueError(
            "This invitation cannot be accepted "
            "as a family-member invitation."
        )

    require_verified_invitation(invitation)

    if not invitation_belongs_to_user(
        invitation=invitation,
        user=user,
    ):
        raise ValueError(
            "This invitation was not issued "
            "for the authenticated user's "
            "contact information."
        )

    if FamilyMember.objects.filter(
        family=invitation.family,
        user=user,
    ).exists():
        raise ValueError(
            "You are already a member of this family."
        )

    member = FamilyMember.objects.create(
        family=invitation.family,
        user=user,
        role=invitation.role,
    )

    now = timezone.now()

    invitation.accepted_by = user
    invitation.status = (
        FamilyInvitation.Status.ACCEPTED
    )
    invitation.accepted_at = now

    invitation.save(
        update_fields=[
            "status",
            "accepted_at",
            "accepted_by",
            "updated_at",
        ]
    )

    create_audit_log(
        family=invitation.family,
        actor=user,
        action=(
            FamilyAuditLog.Action
            .MEMBER_ACCEPTED
        ),
        invitation=invitation,
        metadata={
            "membership_id": member.id,
            "role": member.role,
        },
    )

    return member


# ============================================================
# COMPLETE MEMBER REGISTRATION
# ============================================================

@transaction.atomic
def complete_invitation_registration(
    *,
    token,
    validated_data,
):
    """
    Complete registration for a new family member.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    if invitation.invitation_type != (
        FamilyInvitation
        .InvitationType
        .MEMBER
    ):
        raise ValueError(
            "This invitation is not a "
            "family-member invitation."
        )

    require_verified_invitation(invitation)

    password = validated_data.get("password")

    if not password:
        raise ValueError(
            "Password is required."
        )

    email = (
        invitation.email
        or ""
    ).strip().lower() or None

    phone = (
        invitation.phone_number
        or ""
    ).strip() or None

    if email and User.objects.filter(
        email__iexact=email
    ).exists():
        raise ValueError(
            "An account already exists for this email. "
            "Please sign in and accept the invitation."
        )

    if phone and User.objects.filter(
        phone_number=phone
    ).exists():
        raise ValueError(
            "An account already exists for this phone "
            "number. Please sign in and accept "
            "the invitation."
        )

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

    validate_password(
        password,
        user=None,
    )

    first_name = (
        validated_data.get("first_name")
        or (
            invitation.name.split(" ")[0]
            if invitation.name
            else ""
        )
    )

    last_name = (
        validated_data.get("last_name")
        or ""
    )

    user = User(
        username=username,
        email=email,
        phone_number=phone,
        first_name=first_name,
        last_name=last_name,
        account_status="active",
    )

    user.set_password(password)
    user.save()

    member = FamilyMember.objects.create(
        family=invitation.family,
        user=user,
        role=invitation.role,
    )

    now = timezone.now()

    invitation.accepted_by = user
    invitation.status = (
        FamilyInvitation.Status.ACCEPTED
    )
    invitation.accepted_at = now

    invitation.save(
        update_fields=[
            "status",
            "accepted_at",
            "accepted_by",
            "updated_at",
        ]
    )

    create_audit_log(
        family=invitation.family,
        actor=user,
        action=(
            FamilyAuditLog.Action
            .MEMBER_REGISTERED
        ),
        invitation=invitation,
        metadata={
            "membership_id": member.id,
            "role": member.role,
        },
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
    Complete an existing patient account claim.

    No new Patient is created.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    if invitation.invitation_type != (
        FamilyInvitation
        .InvitationType
        .PATIENT_CLAIM
    ):
        raise ValueError(
            "This invitation is not a "
            "patient claim invitation."
        )

    require_verified_invitation(invitation)

    patient = invitation.patient

    if not patient:
        raise ValueError(
            "This patient claim invitation is "
            "not linked to a patient."
        )

    user = getattr(
        patient,
        "user",
        None,
    )

    if not user:
        raise ValueError(
            "The patient does not have an "
            "associated user account."
        )

    if user.account_status == "active":
        raise ValueError(
            "This patient account is already active."
        )

    password = validated_data.get("password")

    if not password:
        raise ValueError(
            "Password is required."
        )

    validate_password(
        password,
        user=user,
    )

    username = validated_data.get(
        "username"
    )

    if username:
        username = username.strip()

        if User.objects.filter(
            username=username
        ).exclude(
            pk=user.pk
        ).exists():
            raise ValueError(
                "This username is already in use."
            )

        user.username = username

    # --------------------------------------------------------
    # Verified email
    # --------------------------------------------------------

    if invitation.email:

        email = (
            invitation.email
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=user.pk
        ).exists():
            raise ValueError(
                "This email is already associated "
                "with another account."
            )

        user.email = email

    # --------------------------------------------------------
    # Verified phone
    # --------------------------------------------------------

    if invitation.phone_number:

        phone = (
            invitation.phone_number
            .strip()
        )

        if User.objects.filter(
            phone_number=phone
        ).exclude(
            pk=user.pk
        ).exists():
            raise ValueError(
                "This phone number is already associated "
                "with another account."
            )

        user.phone_number = phone

    # --------------------------------------------------------
    # Optional profile data
    # --------------------------------------------------------

    if validated_data.get("first_name"):
        user.first_name = (
            validated_data["first_name"]
        )

    if validated_data.get("last_name"):
        user.last_name = (
            validated_data["last_name"]
        )

    # --------------------------------------------------------
    # Activate
    # --------------------------------------------------------

    user.account_status = "active"
    user.set_password(password)
    user.save()

    # --------------------------------------------------------
    # Consume invitation
    # --------------------------------------------------------

    now = timezone.now()

    invitation.accepted_by = user
    invitation.status = (
        FamilyInvitation.Status.ACCEPTED
    )
    invitation.accepted_at = now

    invitation.save(
        update_fields=[
            "status",
            "accepted_at",
            "accepted_by",
            "updated_at",
        ]
    )

    create_audit_log(
        family=invitation.family,
        actor=user,
        action=(
            FamilyAuditLog.Action
            .PATIENT_CLAIMED
        ),
        invitation=invitation,
        patient=patient,
        metadata={
            "patient_id": patient.id,
        },
    )

    return user, patient