from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UsersListView,
    UserProfileView,
    CustomTokenObtainPairView,
    RegisterUserView,
    LogoutUserView,
    LoginView,
    EnhancedChangePasswordView,
    SendResetCodeView,
    VerifyResetCodeView,
    ResetPasswordView,
    DeactivateAccountView,
)


urlpatterns = [
    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path("auth/login/", CustomTokenObtainPairView.as_view(),name="login",),
    path(
        "auth/register/",
        RegisterUserView.as_view(),
        name="register",
    ),

    path(
        "auth/logout/",
        LogoutUserView.as_view(),
        name="logout",
    ),

    path(
        "auth/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),


    # ========================================================
    # CURRENT USER PROFILE
    # ========================================================

    path(
        "auth/profile/",
        UserProfileView.as_view(),
        name="profile",
    ),


    # ========================================================
    # PASSWORD
    # ========================================================

    # Authenticated password change
    path(
        "auth/password/change/",
        EnhancedChangePasswordView.as_view(),
        name="change-password",
    ),

    # Request password-reset OTP
    path(
        "auth/password/reset/request/",
        SendResetCodeView.as_view(),
        name="password-reset-request",
    ),

    # Verify password-reset OTP
    path(
        "auth/password/reset/verify/",
        VerifyResetCodeView.as_view(),
        name="password-reset-verify",
    ),

    # Set new password using temporary reset token
    path(
        "auth/password/reset/confirm/",
        ResetPasswordView.as_view(),
        name="password-reset-confirm",
    ),


    # ========================================================
    # ACCOUNT
    # ========================================================

    # Deactivate current account
    path(
        "auth/account/deactivate/",
        DeactivateAccountView.as_view(),
        name="account-deactivate",
    ),


    # ========================================================
    # ADMINISTRATION
    # ========================================================

    # List all users
    path(
        "admin/users/",
        UsersListView.as_view(),
        name="admin-users",
    ),
]