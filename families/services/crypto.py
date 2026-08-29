import hashlib
import secrets


# ============================================================
# TOKEN HELPERS
# ============================================================

def generate_invitation_token():
    """
    Generate a cryptographically secure invitation token.

    Only the SHA-256 hash is persisted.

    The raw token must never be persisted.
    """

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    return raw_token, token_hash


def hash_invitation_token(token):
    """
    Hash a raw invitation token for database lookup.
    """

    if not token:
        return ""

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


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
