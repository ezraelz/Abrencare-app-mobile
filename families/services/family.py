from django.db import transaction

from .audit import _create_audit_log
from ..models import Family, FamilyAuditLog, FamilyMember


# ============================================================
# FAMILY
# ============================================================

@transaction.atomic
def create_family(
    *,
    user,
    name,
):
    """
    Create a family and automatically create its owner.
    """

    family = Family.objects.create(
        name=name,
        created_by=user,
    )

    FamilyMember.objects.create(
        family=family,
        user=user,
        role=FamilyMember.Role.OWNER,
        can_view_patient_records=True,
        can_manage_appointments=True,
        can_manage_medications=True,
        can_manage_family_members=True,
        can_manage_family_patients=True,
    )

    _create_audit_log(
        family=family,
        action=FamilyAuditLog.Action.FAMILY_CREATED,
        actor=user,
    )

    return family

