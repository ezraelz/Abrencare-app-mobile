from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Anyone (including anonymous users) can read the catalog — it's public
    marketing/service data, not PHI. Only staff can create/update/delete.

    If your roles are more granular than Django's `is_staff` flag (e.g. a
    dedicated "catalog_manager" group/permission), swap the check below for
    `request.user.has_perm("catalog.change_service")` etc.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
