from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from ..models import PasswordHistory


MAX_PASSWORD_LENGTH = 128
PASSWORD_HISTORY_WINDOW_DAYS = 180
PASSWORD_HISTORY_LIMIT = 10


class PasswordService:
    """
    Centralized password security logic.

    Used by:
        - authenticated password changes
        - password resets
    """

    @classmethod
    def validate_password(cls, user, password):
        errors = []

        if len(password) > MAX_PASSWORD_LENGTH:
            errors.append(
                f"Password must be at most "
                f"{MAX_PASSWORD_LENGTH} characters long."
            )

        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            errors.extend(exc.messages)

        return errors

    @classmethod
    def is_password_in_history(cls, user, new_password):
        window_start = timezone.now() - timedelta(
            days=PASSWORD_HISTORY_WINDOW_DAYS
        )

        history = (
            PasswordHistory.objects
            .filter(
                user=user,
                created_at__gte=window_start,
            )
            .order_by("-created_at")
        )

        for entry in history:
            if entry.check_password(new_password):
                return True

        return False

    @classmethod
    def save_password_history(cls, user, password):
        PasswordHistory.objects.create(
            user=user,
            password=password,
        )

        old_ids = list(
            PasswordHistory.objects
            .filter(user=user)
            .order_by("-created_at")
            .values_list("id", flat=True)[PASSWORD_HISTORY_LIMIT:]
        )

        if old_ids:
            PasswordHistory.objects.filter(
                id__in=old_ids
            ).delete()

    @classmethod
    def validate_new_password(cls, user, password):
        """
        Runs all password security checks.
        """

        errors = cls.validate_password(
            user=user,
            password=password,
        )

        if errors:
            return errors

        if user.check_password(password):
            return [
                "The new password must be different from "
                "your current password."
            ]

        if cls.is_password_in_history(user, password):
            return [
                "You cannot reuse a recently used password."
            ]

        return []

    @classmethod
    @transaction.atomic
    def change_password(cls, user, new_password):
        """
        Change password and save password history atomically.
        """

        user.set_password(new_password)
        user.save(update_fields=["password"])

        cls.save_password_history(
            user=user,
            password=new_password,
        )

    @classmethod
    def revoke_all_refresh_tokens(cls, user):
        """
        Blacklist every outstanding refresh token belonging to
        the user.

        Requires:
            rest_framework_simplejwt.token_blacklist
        """

        outstanding_tokens = OutstandingToken.objects.filter(
            user=user
        )

        for outstanding in outstanding_tokens:
            BlacklistedToken.objects.get_or_create(
                token=outstanding
            )
            