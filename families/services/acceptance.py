from django.db import transaction
from django.utils import timezone

from .audit import _create_audit_log
from .helpers import (
    _invitation_belongs_to_user,
    _require_verified_invitation,
)
from .lookup import _get_invitation
from ..models import FamilyAuditLog, FamilyInvitation, FamilyMember


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
    Accept a family-member invitation for an existing user.

    Requirements:
        - valid invitation
        - MEMBER invitation
        - verified contact
        - authenticated user
        - invitation contact belongs to user
        - user is not already a family member

    The invitation is consumed atomically.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    # --------------------------------------------------------
    # Type
    # --------------------------------------------------------

    if invitation.invitation_type != (
        FamilyInvitation
        .InvitationType
        .MEMBER
    ):
        raise ValueError(
            "This invitation cannot be accepted "
            "as a family-member invitation."
        )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    _require_verified_invitation(
        invitation
    )

    # --------------------------------------------------------
    # Contact ownership
    # --------------------------------------------------------

    if not _invitation_belongs_to_user(
        invitation,
        user,
    ):
        raise ValueError(
            "This invitation was not issued "
            "for the authenticated user's "
            "contact information."
        )

    # --------------------------------------------------------
    # Existing membership
    # --------------------------------------------------------

    existing_membership = (
        FamilyMember.objects
        .filter(
            family=invitation.family,
            user=user,
        )
        .first()
    )

    if existing_membership:
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

    now = timezone.now()

    invitation.accepted_by = user
    invitation.status = (
        FamilyInvitation
        .Status
        .ACCEPTED
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

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    _create_audit_log(
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
