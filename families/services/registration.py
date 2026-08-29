import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.db import transaction
from django.utils import timezone

from .audit import _create_audit_log
from .helpers import _require_verified_invitation
from .lookup import _get_invitation
from ..models import FamilyAuditLog, FamilyInvitation, FamilyMember


User = get_user_model()


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

    The User is created only after contact verification.

    Password validation is delegated to Django's
    configured password validators.

    User creation, membership creation, and invitation
    consumption happen in one transaction.
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
            "This invitation is not a "
            "family-member invitation."
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
    # Contact
    # --------------------------------------------------------

    email = (
        invitation.email
        or ""
    ).strip().lower() or None

    phone = (
        invitation.phone_number
        or ""
    ).strip() or None

    # --------------------------------------------------------
    # Account collision
    # --------------------------------------------------------

    if email:
        existing_user = (
            User.objects
            .filter(email__iexact=email)
            .first()
        )

        if existing_user:
            raise ValueError(
                "An account already exists for this email. "
                "Please sign in and accept the invitation."
            )

    if phone:
        existing_user = (
            User.objects
            .filter(phone_number=phone)
            .first()
        )

        if existing_user:
            raise ValueError(
                "An account already exists for this phone "
                "number. Please sign in and accept "
                "the invitation."
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
    # Validate password
    # --------------------------------------------------------

    validate_password(
        password,
        user=None,
    )

    # --------------------------------------------------------
    # Create account
    # --------------------------------------------------------

    first_name = (
        validated_data.get("first_name")
        or (
            invitation.name.split(" ")[0]
            if invitation.name
            else ""
        )
    )

    last_name = (
        validated_data.get(
            "last_name"
        )
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
            .MEMBER_REGISTERED
        ),
        invitation=invitation,
        metadata={
            "membership_id": member.id,
            "role": member.role,
        },
    )

    return user, member
