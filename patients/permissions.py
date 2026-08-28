from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    """
    User must have an active Patient profile.
    """

    message = "An active patient profile is required."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not user.is_active:
            return False

        return hasattr(user, "patient_profile")


class IsPatientOwner(BasePermission):
    """
    User must own the Patient object.
    """

    message = "You can only access your own patient profile."

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return obj.user_id == request.user.id


class IsEmergencyContactOwner(BasePermission):
    """
    User must own the patient associated with the emergency contact.
    """

    message = "You can only manage your own emergency contacts."

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return obj.patient.user_id == request.user.id


class IsMedicalDocumentOwner(BasePermission):
    """
    User must own the patient associated with the document.
    """

    message = "You can only access your own medical documents."

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return obj.patient.user_id == request.user.id