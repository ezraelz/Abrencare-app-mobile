from rest_framework.permissions import BasePermission


class IsPatientUser(BasePermission):
    """Allows access only to authenticated users linked to a Patient profile."""

    message = "Only patients can access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "patient_profile")
        )


class IsDoctorUser(BasePermission):
    """Allows access only to authenticated users linked to a Doctor profile."""

    message = "Only doctors can access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "doctor")
        )
    