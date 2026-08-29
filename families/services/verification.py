import hmac
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .audit import _create_audit_log
from .constants import (
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
)
from .contact_masking import _mask_contact
from .crypto import generate_otp, hash_otp
from .lookup import _get_invitation
from ..models import FamilyAuditLog, InvitationDelivery


# ============================================================
# REQUEST CONTACT VERIFICATION
# ============================================================

@transaction.atomic
def request_invitation_contact_verification(
    *,
    token,
):
    """
    Generate a new OTP for invitation contact verification.

    Security guarantees:
        - invitation must be valid
        - invitation must be pending
        - resend cooldown is enforced
        - previous OTP is invalidated
        - OTP is hashed before persistence
        - raw OTP is never returned
        - raw OTP is never persisted
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    now = timezone.now()

    # --------------------------------------------------------
    # Resend cooldown
    # --------------------------------------------------------

    if invitation.otp_sent_at:
        elapsed = (
            now - invitation.otp_sent_at
        ).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            remaining = max(
                int(
                    OTP_RESEND_COOLDOWN_SECONDS
                    - elapsed
                ),
                1,
            )

            raise ValueError(
                f"Please wait {remaining} seconds "
                "before requesting another code."
            )

    # --------------------------------------------------------
    # Contact
    # --------------------------------------------------------

    if invitation.email:
        channel = (
            InvitationDelivery
            .Channel
            .EMAIL
        )
        destination = invitation.email

    elif invitation.phone_number:
        channel = (
            InvitationDelivery
            .Channel
            .SMS
        )
        destination = invitation.phone_number

    else:
        raise ValueError(
            "This invitation has no contact information."
        )

    # --------------------------------------------------------
    # Generate OTP
    # --------------------------------------------------------

    otp = generate_otp()

    invitation.otp_hash = hash_otp(otp)

    invitation.otp_expires_at = (
        now
        + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        )
    )

    invitation.otp_sent_at = now
    invitation.otp_attempts = 0
    invitation.otp_locked_at = None

    invitation.save(
        update_fields=[
            "otp_hash",
            "otp_expires_at",
            "otp_sent_at",
            "otp_attempts",
            "otp_locked_at",
            "updated_at",
        ]
    )

    # --------------------------------------------------------
    # Delivery record
    # --------------------------------------------------------

    delivery = InvitationDelivery.objects.create(
        invitation=invitation,
        channel=channel,
        destination=destination,
        status=(
            InvitationDelivery
            .Status
            .PENDING
        ),
    )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    _create_audit_log(
        family=invitation.family,
        action=(
            FamilyAuditLog.Action
            .INVITATION_OTP_REQUESTED
        ),
        invitation=invitation,
        patient=invitation.patient,
        metadata={
            "channel": channel,
            "delivery_id": delivery.id,
        },
    )

    # --------------------------------------------------------
    # Notification
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # The raw OTP is available only in memory.
    #
    # The actual SMS/email provider should be called
    # by the notification/task layer.
    #
    # Do not return otp from this function.
    #
    # --------------------------------------------------------

    return {
        "channel": channel,
        "destination": _mask_contact(
            destination,
            channel,
        ),
        "expires_in": (
            OTP_EXPIRY_MINUTES * 60
        ),
        "delivery_id": delivery.id,
    }


# ============================================================
# VERIFY OTP
# ============================================================

@transaction.atomic
def verify_invitation_otp(
    *,
    token,
    otp,
):
    """
    Verify an invitation OTP atomically.

    The invitation row is locked during verification.

    Every failed attempt is persisted.

    A fifth failed attempt locks OTP verification.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    now = timezone.now()

    # --------------------------------------------------------
    # Already locked
    # --------------------------------------------------------

    if invitation.otp_locked_at:
        raise ValueError(
            "Verification is locked. "
            "Please request a new code."
        )

    # --------------------------------------------------------
    # No OTP
    # --------------------------------------------------------

    if not invitation.otp_hash:
        raise ValueError(
            "No verification code has been requested."
        )

    # --------------------------------------------------------
    # Expired OTP
    # --------------------------------------------------------

    if (
        not invitation.otp_expires_at
        or invitation.otp_expires_at <= now
    ):
        raise ValueError(
            "The verification code has expired. "
            "Please request a new code."
        )

    # --------------------------------------------------------
    # Attempts already exhausted
    # --------------------------------------------------------

    if invitation.otp_attempts >= OTP_MAX_ATTEMPTS:
        invitation.otp_locked_at = now
        invitation.save(
            update_fields=[
                "otp_locked_at",
                "updated_at",
            ]
        )

        _create_audit_log(
            family=invitation.family,
            action=(
                FamilyAuditLog.Action
                .OTP_LOCKED
            ),
            invitation=invitation,
            patient=invitation.patient,
        )

        raise ValueError(
            "Too many verification attempts. "
            "Please request a new code."
        )

    # --------------------------------------------------------
    # Increment attempt BEFORE comparison
    # --------------------------------------------------------

    invitation.otp_attempts += 1

    is_valid = hmac.compare_digest(
        hash_otp(otp),
        invitation.otp_hash,
    )

    # --------------------------------------------------------
    # Invalid OTP
    # --------------------------------------------------------

    if not is_valid:
        if (
            invitation.otp_attempts
            >= OTP_MAX_ATTEMPTS
        ):
            invitation.otp_locked_at = now

            invitation.save(
                update_fields=[
                    "otp_attempts",
                    "otp_locked_at",
                    "updated_at",
                ]
            )

            _create_audit_log(
                family=invitation.family,
                action=(
                    FamilyAuditLog.Action
                    .OTP_LOCKED
                ),
                invitation=invitation,
                patient=invitation.patient,
                metadata={
                    "reason": (
                        "maximum_attempts_exceeded"
                    ),
                },
            )

            raise ValueError(
                "Too many verification attempts. "
                "Please request a new code."
            )

        invitation.save(
            update_fields=[
                "otp_attempts",
                "updated_at",
            ]
        )

        remaining = (
            OTP_MAX_ATTEMPTS
            - invitation.otp_attempts
        )

        raise ValueError(
            "Invalid verification code. "
            f"{remaining} attempts remaining."
        )

    # --------------------------------------------------------
    # Successful verification
    # --------------------------------------------------------

    invitation.contact_verified_at = now
    invitation.otp_hash = ""
    invitation.otp_expires_at = None
    invitation.otp_attempts = 0
    invitation.otp_locked_at = None

    invitation.save(
        update_fields=[
            "contact_verified_at",
            "otp_hash",
            "otp_expires_at",
            "otp_attempts",
            "otp_locked_at",
            "updated_at",
        ]
    )

    _create_audit_log(
        family=invitation.family,
        action=(
            FamilyAuditLog.Action
            .INVITATION_CONTACT_VERIFIED
        ),
        invitation=invitation,
        patient=invitation.patient,
    )

    return {
        "verified": True,
        "verified_at": now,
    }
