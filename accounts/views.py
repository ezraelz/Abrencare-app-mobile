import logging

from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    EnhancedChangePasswordSerializer,
)
from .services.password import PasswordService
from .services.password_reset import PasswordResetService
from .tasks import (
    send_password_reset_email,
    send_password_reset_confirmation_email,
)
from .throttles import (
    LoginThrottle,
    RegistrationThrottle,
    PasswordResetRequestThrottle,
    PasswordResetVerifyThrottle,
    PasswordResetCompleteThrottle,
)


logger = logging.getLogger("security")


# ============================================================
# SHARED SECURITY MIXINS
# ============================================================


class ClientInfoMixin:
    """
    Safely retrieve the client's IP address.

    By default, REMOTE_ADDR is used.

    X-Forwarded-For is only trusted when explicitly enabled
    through TRUST_X_FORWARDED_FOR in Django settings.

    IMPORTANT:
        Only enable TRUST_X_FORWARDED_FOR when your reverse proxy
        is configured to overwrite/sanitize the header.
    """

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if (
            forwarded_for
            and getattr(
                settings,
                "TRUST_X_FORWARDED_FOR",
                False,
            )
        ):
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


class SecurityLogMixin(ClientInfoMixin):
    """
    Centralized security logging.

    NEVER log:
        - passwords
        - OTP codes
        - access tokens
        - refresh tokens
        - reset tokens
        - authorization headers
    """

    def log_event(
        self,
        message,
        user=None,
        request=None,
        **extra,
    ):
        payload = dict(extra)

        if user is not None:
            payload["user_id"] = user.id

        if request is not None:
            payload["ip_address"] = self.get_client_ip(
                request
            )

        logger.info(
            message,
            extra=payload,
        )


# ============================================================
# USER LIST
# ============================================================


class UsersListView(generics.ListAPIView):
    """
    List users.

    Only administrators are allowed to access this endpoint.
    """

    serializer_class = UserSerializer

    permission_classes = [
        permissions.IsAdminUser
    ]

    def get_queryset(self):
        return (
            User.objects
            .all()
            .order_by("-id")
        )


# ============================================================
# CURRENT USER PROFILE
# ============================================================


class UserProfileView(APIView):
    """
    Get or update the currently authenticated user's profile.
    This endpoint intentionally does not accept a user ID.
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):
        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# JWT LOGIN
# ============================================================


class CustomTokenObtainPairView(
    TokenObtainPairView
):
    """
    JWT login endpoint.

    Login attempts are throttled to reduce brute-force attacks.
    """

    serializer_class = (
        CustomTokenObtainPairSerializer
    )

    throttle_classes = [
        LoginThrottle
    ]


# ============================================================
# USER REGISTRATION
# ============================================================


class RegisterUserView(APIView):
    """
    Register a new user.

    Registration is publicly accessible but throttled.
    """

    permission_classes = [
        permissions.AllowAny
    ]

    throttle_classes = [
        RegistrationThrottle
    ]

    def post(self, request):
        serializer = UserCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        with transaction.atomic():
            user = serializer.save()

        return Response(
            {
                "message": (
                    "User registered successfully."
                ),
                "user": UserSerializer(
                    user
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# LOGOUT
# ============================================================


class LogoutUserView(
    SecurityLogMixin,
    APIView,
):
    """
    Logout the current user by blacklisting the supplied
    refresh token.

    The supplied refresh token must belong to the currently
    authenticated user.
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):
        refresh_token = (
            request.data.get("refresh")
            or ""
        ).strip()

        if not refresh_token:
            return Response(
                {
                    "error": (
                        "Refresh token is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(
                refresh_token
            )

            token_user_id = str(
                token.get("user_id")
            )

            current_user_id = str(
                request.user.id
            )

            # Prevent a user from blacklisting another
            # user's refresh token.
            if token_user_id != current_user_id:
                logger.warning(
                    "Refresh token ownership mismatch during logout",
                    extra={
                        "user_id": request.user.id,
                        "ip_address": (
                            self.get_client_ip(request)
                        ),
                    },
                )

                return Response(
                    {
                        "error": (
                            "Invalid refresh token."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token.blacklist()

            self.log_event(
                "User logged out",
                user=request.user,
                request=request,
            )

            return Response(
                {
                    "message": (
                        "Logged out successfully."
                    )
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.warning(
                "Invalid refresh token supplied during logout",
                extra={
                    "user_id": request.user.id,
                    "ip_address": (
                        self.get_client_ip(request)
                    ),
                },
            )

            return Response(
                {
                    "error": (
                        "Invalid or expired "
                        "refresh token."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# CHANGE PASSWORD
# ============================================================


class EnhancedChangePasswordView(
    SecurityLogMixin,
    APIView,
):
    """
    Change password for the currently authenticated user.

    Security features:

    - authenticated-only access
    - current password verification
    - Django password validators
    - maximum password length
    - current-password reuse protection
    - password history protection
    - password history storage
    - atomic password update
    - revocation of all refresh tokens
    - security logging
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):
        serializer = EnhancedChangePasswordSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = request.user

        current_password = (
            serializer.validated_data[
                "current_password"
            ]
        )

        new_password = (
            serializer.validated_data[
                "new_password"
            ]
        )

        # ----------------------------------------------------
        # Verify current password
        # ----------------------------------------------------

        if not user.check_password(
            current_password
        ):
            return Response(
                {
                    "error": (
                        "Current password is incorrect."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate new password
        # ----------------------------------------------------

        validation_errors = (
            PasswordService.validate_new_password(
                user=user,
                password=new_password,
            )
        )

        if validation_errors:
            return Response(
                {
                    "error": validation_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Change password atomically
        # ----------------------------------------------------

        with transaction.atomic():

            PasswordService.change_password(
                user=user,
                new_password=new_password,
            )

            # Security-first approach:
            # invalidate every outstanding refresh token.
            #
            # The frontend should clear its JWT tokens and
            # require the user to authenticate again.
            PasswordService.revoke_all_refresh_tokens(
                user
            )

        # ----------------------------------------------------
        # Keep Django session alive if session auth is used
        # ----------------------------------------------------

        update_session_auth_hash(
            request,
            user,
        )

        self.log_event(
            "Password changed",
            user=user,
            request=request,
        )

        return Response(
            {
                "message": (
                    "Password changed successfully. "
                    "Please sign in again on other devices."
                ),
                "timestamp": (
                    timezone.now().isoformat()
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# PASSWORD RESET - REQUEST CODE
# ============================================================


class SendResetCodeView(
    SecurityLogMixin,
    APIView,
):
    """
    Start a password reset.

    Security features:

    - anonymous access
    - IP-based throttling
    - email cooldown
    - generic response
    - no account enumeration
    - hashed OTP storage
    - asynchronous email delivery
    """

    permission_classes = [
        permissions.AllowAny
    ]

    throttle_classes = [
        PasswordResetRequestThrottle
    ]

    GENERIC_SUCCESS_MESSAGE = (
        "If the email exists, a reset code has been sent."
    )

    def post(self, request):
        email = (
            PasswordResetService
            .normalize_email(
                request.data.get("email")
            )
        )

        if not email:
            return Response(
                {
                    "error": "Email is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Email-based cooldown
        # ----------------------------------------------------
        #
        # This prevents someone from repeatedly requesting
        # reset emails for the same account.
        #
        # We still return the generic message so the attacker
        # cannot determine whether the email exists.

        if PasswordResetService.is_on_cooldown(
            email
        ):
            return Response(
                {
                    "message": (
                        self.GENERIC_SUCCESS_MESSAGE
                    )
                },
                status=status.HTTP_200_OK,
            )

        # Set cooldown even if the account does not exist.
        PasswordResetService.set_cooldown(
            email
        )

        # ----------------------------------------------------
        # Find user
        # ----------------------------------------------------

        try:
            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:
            return Response(
                {
                    "message": (
                        self.GENERIC_SUCCESS_MESSAGE
                    )
                },
                status=status.HTTP_200_OK,
            )

        # Never reveal disabled accounts.
        if not user.is_active:
            return Response(
                {
                    "message": (
                        self.GENERIC_SUCCESS_MESSAGE
                    )
                },
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # Generate and store reset session
        # ----------------------------------------------------

        code = (
            PasswordResetService
            .create_reset_session(
                user
            )
        )

        # ----------------------------------------------------
        # Send email asynchronously
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # Never log the code.
        #

        send_password_reset_email.delay(
            email=email,
            username=(
                user.first_name
                or user.username
            ),
            code=code,
        )

        self.log_event(
            "Password reset requested",
            user=user,
            request=request,
        )

        return Response(
            {
                "message": (
                    self.GENERIC_SUCCESS_MESSAGE
                )
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# PASSWORD RESET - VERIFY CODE
# ============================================================


class VerifyResetCodeView(
    SecurityLogMixin,
    APIView,
):
    """
    Verify a password-reset OTP.

    A successful verification produces a short-lived,
    one-time reset token.

    The OTP itself is not used again after verification.
    """

    permission_classes = [
        permissions.AllowAny
    ]

    throttle_classes = [
        PasswordResetVerifyThrottle
    ]

    def post(self, request):
        email = (
            PasswordResetService
            .normalize_email(
                request.data.get("email")
            )
        )

        code = (
            request.data.get("code")
            or ""
        ).strip()

        if not email or not code:
            return Response(
                {
                    "error": (
                        "Email and code are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate OTP format
        # ----------------------------------------------------

        if (
            len(code) != 6
            or not code.isdigit()
        ):
            return Response(
                {
                    "error": "Invalid reset code."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Verify OTP
        # ----------------------------------------------------

        result = (
            PasswordResetService
            .verify_otp(
                email=email,
                submitted_code=code,
            )
        )

        if not result["success"]:
            return Response(
                {
                    "error": result["error"]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.log_event(
            "Password reset code verified",
            request=request,
        )

        return Response(
            {
                "message": (
                    "Code verified successfully."
                ),
                "reset_token": (
                    result["reset_token"]
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# PASSWORD RESET - SET NEW PASSWORD
# ============================================================


class ResetPasswordView(
    SecurityLogMixin,
    APIView,
):
    """
    Complete password reset using the temporary reset token.

    The OTP is NOT submitted again here.

    Request:

        {
            "reset_token": "...",
            "new_password": "..."
        }
    """

    permission_classes = [
        permissions.AllowAny
    ]

    throttle_classes = [
        PasswordResetCompleteThrottle
    ]

    def post(self, request):
        reset_token = (
            request.data.get(
                "reset_token"
            )
            or ""
        ).strip()

        new_password = (
            request.data.get(
                "new_password"
            )
            or ""
        )

        if not reset_token or not new_password:
            return Response(
                {
                    "error": (
                        "Reset token and new password "
                        "are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Consume reset token
        # ----------------------------------------------------
        #
        # The token is one-time-use.
        #

        user_id = (
            PasswordResetService
            .consume_reset_token(
                reset_token
            )
        )

        if not user_id:
            return Response(
                {
                    "error": (
                        "Reset session has expired "
                        "or is invalid."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Get user
        # ----------------------------------------------------

        try:
            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Reset session has expired "
                        "or is invalid."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Never reveal the actual reason why the reset
        # session cannot be used.
        if not user.is_active:
            return Response(
                {
                    "error": (
                        "Reset session has expired "
                        "or is invalid."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate password
        # ----------------------------------------------------

        validation_errors = (
            PasswordService.validate_new_password(
                user=user,
                password=new_password,
            )
        )

        if validation_errors:
            return Response(
                {
                    "error": validation_errors
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Change password
        # ----------------------------------------------------

        with transaction.atomic():

            PasswordService.change_password(
                user=user,
                new_password=new_password,
            )

            # Password reset invalidates ALL existing
            # refresh tokens.
            PasswordService.revoke_all_refresh_tokens(
                user
            )

        # ----------------------------------------------------
        # Security logging
        # ----------------------------------------------------

        self.log_event(
            "Password reset successfully",
            user=user,
            request=request,
        )

        # ----------------------------------------------------
        # Confirmation email
        # ----------------------------------------------------

        send_password_reset_confirmation_email.delay(
            email=user.email,
            username=(
                user.first_name
                or user.username
            ),
        )

        return Response(
            {
                "message": (
                    "Password reset successfully. "
                    "Please sign in with your new password."
                )
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# ACCOUNT DEACTIVATION
# ============================================================


class DeactivateAccountView(
    SecurityLogMixin,
    APIView,
):
    """
    Deactivate the currently authenticated account.

    This does not permanently delete the user.

    All outstanding refresh tokens are revoked.
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):
        user = request.user

        # ----------------------------------------------------
        # Protect superuser accounts
        # ----------------------------------------------------

        if user.is_superuser:
            return Response(
                {
                    "error": (
                        "Superuser accounts cannot "
                        "be deactivated from this endpoint."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Deactivate account
        # ----------------------------------------------------

        with transaction.atomic():

            user.is_active = False

            user.save(
                update_fields=[
                    "is_active"
                ]
            )

            # Immediately revoke all refresh tokens.
            PasswordService.revoke_all_refresh_tokens(
                user
            )

        self.log_event(
            "Account deactivated",
            user=user,
            request=request,
        )

        return Response(
            {
                "message": (
                    "Your account has been "
                    "deactivated successfully."
                )
            },
            status=status.HTTP_200_OK,
        )