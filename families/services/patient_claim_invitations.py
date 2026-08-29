from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .audit import _create_audit_log
from .constants import INVITATION_EXPIRY_DAYS
from .crypto import generate_invitation_token
from ..models import FamilyAuditLog, FamilyInvitation


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
    # Ensure contact matches patient account
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

    _create_audit_log(
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
