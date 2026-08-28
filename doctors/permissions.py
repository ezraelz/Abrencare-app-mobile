from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """
    Allows access only to staff users.
    """

    message = "Administrator permission is required."

    def has_permission(self, request, view):

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsDoctor(BasePermission):
    """
    Allows access only to users who have
    an approved doctor profile.
    """

    message = (
        "An approved doctor account is required."
    )

    def has_permission(self, request, view):

        if not (
            request.user
            and request.user.is_authenticated
        ):
            return False

        try:
            doctor = request.user.doctor
        except AttributeError:
            return False

        return (
            request.user.is_active
            and doctor.approval_status
            == doctor.ApprovalStatus.APPROVED
        )


class IsDoctorOwner(BasePermission):
    """
    Allows access only when the authenticated
    user owns the doctor profile.
    """

    message = (
        "You do not have permission "
        "to modify this doctor."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):

        return (
            obj.user_id
            == request.user.id
        )


class IsApprovedDoctorOwner(BasePermission):
    """
    Ensures the authenticated user owns the doctor
    profile and that the doctor is approved.
    """

    message = (
        "You must be an approved doctor "
        "to perform this action."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):

        return (
            obj.user_id == request.user.id
            and request.user.is_active
            and obj.approval_status
            == obj.ApprovalStatus.APPROVED
        )
    