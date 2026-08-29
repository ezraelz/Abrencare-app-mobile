from rest_framework.permissions import BasePermission

from .models import FamilyMember


class IsFamilyMember(BasePermission):
    """
    Allows access only to authenticated users who belong
    to the requested family.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        family_id = view.kwargs.get("family_id")

        if not family_id:
            family_id = view.kwargs.get("pk")

        if not family_id:
            return False

        return FamilyMember.objects.filter(
            family_id=family_id,
            user=request.user,
        ).exists()


class IsFamilyOwner(BasePermission):
    """
    Only the family owner can perform owner-level actions.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        family_id = view.kwargs.get("family_id")

        if not family_id:
            family_id = view.kwargs.get("pk")

        if not family_id:
            return False

        return FamilyMember.objects.filter(
            family_id=family_id,
            user=request.user,
            role=FamilyMember.Role.OWNER,
        ).exists()


class CanManageFamilyMembers(BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        family_id = view.kwargs.get("family_id")

        return FamilyMember.objects.filter(
            family_id=family_id,
            user=request.user,
            can_manage_family_members=True,
        ).exists()


class CanManageFamilyPatients(BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        family_id = view.kwargs.get("family_id")

        return FamilyMember.objects.filter(
            family_id=family_id,
            user=request.user,
            can_manage_family_patients=True,
        ).exists()
    