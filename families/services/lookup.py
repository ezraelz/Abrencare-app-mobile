from django.utils import timezone

from .audit import _create_audit_log
from .crypto import hash_invitation_token
from ..models import FamilyAuditLog, FamilyInvitation


# ============================================================
# INVITATION LOOKUP
# ============================================================

def _get_invitation(
    token,
    *,
    for_update=False,
):
    """
    Resolve an invitation from a raw token.

    When for_update=True, the invitation row is locked
    for the duration of the surrounding transaction.

    This is required for single-use operations such as:
        - OTP verification
        - accepting invitations
        - registration
        - patient claims
    """

    if not token:
        raise ValueError(
            "Invitation token is required."
        )

    token_hash = hash_invitation_token(token)

    queryset = FamilyInvitation.objects.select_related(
        "family",
        "invited_by",
        "accepted_by",
        "patient",
        "patient__user",
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

            _create_audit_log(
                family=invitation.family,
                action=(
                    FamilyAuditLog.Action
                    .INVITATION_EXPIRED
                ),
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
    Public/service-level invitation lookup.

    Does not lock the database row.
    """

    return _get_invitation(
        token,
        for_update=False,
    )
