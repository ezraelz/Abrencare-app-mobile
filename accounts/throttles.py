from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegistrationThrottle(AnonRateThrottle):
    scope = "registration"


class PasswordResetRequestThrottle(AnonRateThrottle):
    scope = "password_reset_request"


class PasswordResetVerifyThrottle(AnonRateThrottle):
    scope = "password_reset_verify"


class PasswordResetCompleteThrottle(AnonRateThrottle):
    scope = "password_reset_complete"