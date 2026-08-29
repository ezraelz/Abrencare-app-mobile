from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.db import transaction
from django.utils import timezone

from .audit import _create_audit_log
from .helpers import _require_verified_invitation
from .lookup import _get_invitation
from ..models import FamilyAuditLog, FamilyInvitation


User = get_user_model()


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

    This never creates a new Patient.

    The existing:

        User
        Patient
        FamilyPatient

    records are retained.

    The pending User is activated and receives
    a password.
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
        .PATIENT_CLAIM
    ):
        raise ValueError(
            "This invitation is not a "
            "patient claim invitation."
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
    # Validate password
    # --------------------------------------------------------

    validate_password(
        password,
        user=user,
    )

    # --------------------------------------------------------
    # Username
    # --------------------------------------------------------

    username = validated_data.get(
        "username"
    )

    if username:
        username = username.strip()

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
    # Verified contact
    # --------------------------------------------------------

    if invitation.email:
        email = (
            invitation.email
            .strip()
            .lower()
        )

        existing_email_user = (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=user.pk)
            .first()
        )

        if existing_email_user:
            raise ValueError(
                "This email is already associated "
                "with another account."
            )

        user.email = email

    if invitation.phone_number:
        phone = (
            invitation.phone_number
            .strip()
        )

        existing_phone_user = (
            User.objects
            .filter(phone_number=phone)
            .exclude(pk=user.pk)
            .first()
        )

        if existing_phone_user:
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
    # Activate account
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
            .PATIENT_CLAIMED
        ),
        invitation=invitation,
        patient=patient,
        metadata={
            "patient_id": patient.id,
        },
    )

    return user, patient
