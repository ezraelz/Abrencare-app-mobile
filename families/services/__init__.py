"""
Family invitation / membership / patient-claim services.

This package is a drop-in replacement for the old single-file
``services.py`` module. Every name that used to live in that
file (including the "private" underscore-prefixed helpers) is
re-exported here, so existing imports such as::

    from .services import invite_family_member
    from .services import _get_invitation

continue to work unchanged.
"""

from .acceptance import accept_invitation
from .audit import _create_audit_log
from .constants import (
    INVITATION_EXPIRY_DAYS,
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
)
from .contact_masking import _mask_contact
from .crypto import (
    generate_invitation_token,
    generate_otp,
    hash_invitation_token,
    hash_otp,
)
from .family import create_family
from .family_patients import create_family_patient
from .helpers import (
    _invitation_belongs_to_user,
    _require_verified_invitation,
)
from .lookup import _get_invitation, get_invitation_by_token
from .member_invitations import invite_family_member
from .patient_claim_completion import complete_patient_claim
from .patient_claim_invitations import create_patient_claim_invitation
from .registration import complete_invitation_registration
from .verification import (
    request_invitation_contact_verification,
    verify_invitation_otp,
)

__all__ = [
    "accept_invitation",
    "complete_invitation_registration",
    "complete_patient_claim",
    "create_family",
    "create_family_patient",
    "create_patient_claim_invitation",
    "generate_invitation_token",
    "generate_otp",
    "get_invitation_by_token",
    "hash_invitation_token",
    "hash_otp",
    "invite_family_member",
    "request_invitation_contact_verification",
    "verify_invitation_otp",
    "INVITATION_EXPIRY_DAYS",
    "OTP_EXPIRY_MINUTES",
    "OTP_MAX_ATTEMPTS",
    "OTP_RESEND_COOLDOWN_SECONDS",
    # Private helpers kept importable for backward compatibility
    # / test access, matching the original module's surface.
    "_create_audit_log",
    "_get_invitation",
    "_invitation_belongs_to_user",
    "_mask_contact",
    "_require_verified_invitation",
]
