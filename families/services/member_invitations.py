from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .audit import _create_audit_log
from .constants import INVITATION_EXPIRY_DAYS
from .crypto import generate_invitation_token
from ..models import FamilyAuditLog, FamilyInvitation, FamilyMember


User = get_user_model()


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

    No User is created at this stage.

    The recipient can later:
        - accept as an existing authenticated user
        - complete registration as a new user
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
    # Find existing account
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
    # Prevent duplicate membership
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

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    _create_audit_log(
        family=family,
        actor=invited_by,
        action=(
            FamilyAuditLog.Action
            .MEMBER_INVITED
        ),
        invitation=invitation,
        metadata={
            "role": invitation.role,
            "cancelled_previous_invitations": (
                cancelled_count
            ),
        },
    )

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    #
    # raw_token exists only in application memory.
    #
    # The notification layer should consume it immediately.
    #
    # Do NOT persist it.
    #
    # Do NOT log it.
    #
    # Do NOT include it in audit metadata.
    #
    # --------------------------------------------------------

    return invitation, raw_token
