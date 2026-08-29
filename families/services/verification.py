import hashlib
import hmac
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ..models import (
    FamilyInvitation,
    InvitationDelivery,
    FamilyAuditLog,
)

from .audit import create_audit_log
from .invitation import _get_invitation


OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


# ============================================================
# OTP HELPERS
# ============================================================

def generate_otp():
    """
    Generate a cryptographically secure six-digit OTP.
    """

    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp):
    """
    Hash an OTP before persistence.
    """

    if not otp:
        return ""

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


# ============================================================
# CONTACT MASKING
# ============================================================

def mask_contact(
    value,
    channel,
):
    """
    Mask email or phone information before exposing it.
    """

    if not value:
        return ""

    if channel == "email":

        if "@" not in value:
            return "***"

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

    if len(value) <= 4:
        return "*" * len(value)

    return (
        "*" * (len(value) - 4)
        + value[-4:]
    )


# ============================================================
# REQUEST OTP
# ============================================================

@transaction.atomic
def request_invitation_contact_verification(
    *,
    token,
):
    """
    Generate and persist a new invitation OTP.

    The raw OTP is intentionally NOT returned.

    Notification delivery should happen through the
    notification/task layer.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    now = timezone.now()

    # --------------------------------------------------------
    # Cooldown
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
    # Delivery
    # --------------------------------------------------------

    delivery = InvitationDelivery.objects.create(
        invitation=invitation,
        channel=channel,
        destination=destination,
        status=InvitationDelivery.Status.PENDING,
    )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    create_audit_log(
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

    # IMPORTANT:
    # `otp` exists only in local memory.
    #
    # Do not:
    #   - return it
    #   - log it
    #   - store it
    #   - audit it

    return {
        "channel": channel,
        "destination": mask_contact(
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
    Atomically verify an invitation OTP.
    """

    invitation = _get_invitation(
        token,
        for_update=True,
    )

    now = timezone.now()

    # --------------------------------------------------------
    # Locked
    # --------------------------------------------------------

    if invitation.otp_locked_at:
        raise ValueError(
            "Verification is locked. "
            "Please request a new code."
        )

    # --------------------------------------------------------
    # Missing OTP
    # --------------------------------------------------------

    if not invitation.otp_hash:
        raise ValueError(
            "No verification code has been requested."
        )

    # --------------------------------------------------------
    # Expired
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
    # Attempt limit
    # --------------------------------------------------------

    if invitation.otp_attempts >= OTP_MAX_ATTEMPTS:

        invitation.otp_locked_at = now

        invitation.save(
            update_fields=[
                "otp_locked_at",
                "updated_at",
            ]
        )

        create_audit_log(
            family=invitation.family,
            action=FamilyAuditLog.Action.OTP_LOCKED,
            invitation=invitation,
            patient=invitation.patient,
        )

        raise ValueError(
            "Too many verification attempts. "
            "Please request a new code."
        )

    # --------------------------------------------------------
    # Increment BEFORE comparison
    # --------------------------------------------------------

    invitation.otp_attempts += 1

    is_valid = hmac.compare_digest(
        hash_otp(otp),
        invitation.otp_hash,
    )

    # --------------------------------------------------------
    # Invalid
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

            create_audit_log(
                family=invitation.family,
                action=FamilyAuditLog.Action.OTP_LOCKED,
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

    create_audit_log(
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