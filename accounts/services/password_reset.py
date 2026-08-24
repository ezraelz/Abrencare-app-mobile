import hashlib
import hmac
import secrets
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone


class PasswordResetService:
    """
    Handles the complete password-reset state machine.

    Flow:

        email
          ↓
        OTP
          ↓
        verify OTP
          ↓
        reset token
          ↓
        set password
    """

    OTP_LENGTH = 6

    OTP_TIMEOUT = 10 * 60
    RESET_TOKEN_TIMEOUT = 15 * 60

    MAX_OTP_ATTEMPTS = 5

    REQUEST_COOLDOWN = 60

    OTP_CHARS = "0123456789"

    @staticmethod
    def normalize_email(email):
        return (email or "").strip().lower()

    @staticmethod
    def session_key(email):
        return f"password_reset:session:{email}"

    @staticmethod
    def cooldown_key(email):
        return f"password_reset:cooldown:{email}"

    @staticmethod
    def reset_token_key(token_hash):
        return f"password_reset:token:{token_hash}"

    @classmethod
    def hash_value(cls, value):
        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    @classmethod
    def generate_otp(cls):
        return "".join(
            secrets.choice(cls.OTP_CHARS)
            for _ in range(cls.OTP_LENGTH)
        )

    @classmethod
    def generate_reset_token(cls):
        return secrets.token_urlsafe(32)

    @classmethod
    def create_reset_session(cls, user):
        email = cls.normalize_email(user.email)

        otp = cls.generate_otp()
        otp_hash = cls.hash_value(otp)

        session = {
            "user_id": user.id,
            "otp_hash": otp_hash,
            "created_at": timezone.now().isoformat(),
            "attempts": 0,
        }

        cache.set(
            cls.session_key(email),
            session,
            timeout=cls.OTP_TIMEOUT,
        )

        return otp

    @classmethod
    def is_on_cooldown(cls, email):
        return cache.get(cls.cooldown_key(email)) is not None

    @classmethod
    def set_cooldown(cls, email):
        cache.set(
            cls.cooldown_key(email),
            True,
            timeout=cls.REQUEST_COOLDOWN,
        )

    @classmethod
    def get_session(cls, email):
        return cache.get(cls.session_key(email))

    @classmethod
    def verify_otp(cls, email, submitted_code):
        """
        Verify OTP.

        Returns:

            {
                "success": True,
                "reset_token": "..."
            }

        or:

            {
                "success": False,
                "error": "..."
            }
        """

        key = cls.session_key(email)

        session = cache.get(key)

        if not session:
            return {
                "success": False,
                "error": "Reset code has expired or is invalid.",
            }

        submitted_hash = cls.hash_value(
            submitted_code
        )

        expected_hash = session.get("otp_hash")

        if not expected_hash or not hmac.compare_digest(
            submitted_hash,
            expected_hash,
        ):
            attempts = session.get("attempts", 0) + 1

            if attempts >= cls.MAX_OTP_ATTEMPTS:
                cache.delete(key)

                return {
                    "success": False,
                    "error": (
                        "Too many failed attempts. "
                        "Please request a new code."
                    ),
                }

            session["attempts"] = attempts

            remaining_timeout = cls.get_remaining_timeout(
                session
            )

            cache.set(
                key,
                session,
                timeout=remaining_timeout,
            )

            return {
                "success": False,
                "error": "Invalid reset code.",
            }

        reset_token = cls.generate_reset_token()

        token_hash = cls.hash_value(reset_token)

        reset_session = {
            "user_id": session["user_id"],
            "created_at": timezone.now().isoformat(),
        }

        cache.set(
            cls.reset_token_key(token_hash),
            reset_session,
            timeout=cls.RESET_TOKEN_TIMEOUT,
        )

        # OTP is one-time-use.
        cache.delete(key)

        return {
            "success": True,
            "reset_token": reset_token,
        }

    @classmethod
    def consume_reset_token(cls, reset_token):
        """
        Retrieve and consume a reset token.

        Returns user_id or None.
        """

        if not reset_token:
            return None

        token_hash = cls.hash_value(reset_token)

        key = cls.reset_token_key(token_hash)

        data = cache.get(key)

        if not data:
            return None

        # One-time use.
        cache.delete(key)

        return data.get("user_id")

    @classmethod
    def get_remaining_timeout(cls, session):
        try:
            created_at = timezone.datetime.fromisoformat(
                session["created_at"]
            )

            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(
                    created_at
                )

            elapsed = (
                timezone.now() - created_at
            ).total_seconds()

            remaining = int(
                cls.OTP_TIMEOUT - elapsed
            )

            return max(1, remaining)

        except (
            KeyError,
            ValueError,
            TypeError,
        ):
            return 1