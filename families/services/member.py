from django.db import transaction

from ..models import (
    Family,
    FamilyMember,
    FamilyAuditLog,
)

from .audit import create_audit_log


# ============================================================
# CREATE FAMILY OWNER
# ============================================================

@transaction.atomic
def create_family_owner(
    *,
    family,
    user,
):
    """
    Create the initial owner membership for a family.
    """

    if not family:
        raise ValueError("Family is required.")

    if not user:
        raise ValueError("User is required.")

    if FamilyMember.objects.filter(
        family=family,
        role=FamilyMember.Role.OWNER,
    ).exists():
        raise ValueError(
            "This family already has an owner."
        )

    if FamilyMember.objects.filter(
        family=family,
        user=user,
    ).exists():
        raise ValueError(
            "This user is already a member of the family."
        )

    member = FamilyMember.objects.create(
        family=family,
        user=user,
        role=FamilyMember.Role.OWNER,
        can_view_patient_records=True,
        can_manage_appointments=True,
        can_manage_medications=True,
        can_manage_family_members=True,
        can_manage_family_patients=True,
    )

    create_audit_log(
        family=family,
        actor=user,
        action=FamilyAuditLog.Action.MEMBER_CREATED,
        metadata={
            "membership_id": member.id,
            "role": member.role,
        },
    )

    return member


# ============================================================
# ADD FAMILY MEMBER
# ============================================================

@transaction.atomic
def add_family_member(
    *,
    family,
    user,
    role=FamilyMember.Role.MEMBER,
    can_view_patient_records=False,
    can_manage_appointments=False,
    can_manage_medications=False,
    can_manage_family_members=False,
    can_manage_family_patients=False,
    actor=None,
):
    """
    Directly add an existing user to a family.

    Invitation-based users should normally go through
    accept_invitation() instead.
    """

    if not family:
        raise ValueError("Family is required.")

    if not user:
        raise ValueError("User is required.")

    valid_roles = dict(
        FamilyMember.Role.choices
    )

    if role not in valid_roles:
        raise ValueError(
            "Invalid family member role."
        )

    if FamilyMember.objects.filter(
        family=family,
        user=user,
    ).exists():
        raise ValueError(
            "This user is already a member of the family."
        )

    if role == FamilyMember.Role.OWNER:
        if FamilyMember.objects.filter(
            family=family,
            role=FamilyMember.Role.OWNER,
        ).exists():
            raise ValueError(
                "This family already has an owner."
            )

    member = FamilyMember.objects.create(
        family=family,
        user=user,
        role=role,
        can_view_patient_records=(
            can_view_patient_records
        ),
        can_manage_appointments=(
            can_manage_appointments
        ),
        can_manage_medications=(
            can_manage_medications
        ),
        can_manage_family_members=(
            can_manage_family_members
        ),
        can_manage_family_patients=(
            can_manage_family_patients
        ),
    )

    create_audit_log(
        family=family,
        actor=actor,
        action=FamilyAuditLog.Action.MEMBER_CREATED,
        metadata={
            "membership_id": member.id,
            "member_user_id": user.id,
            "role": member.role,
        },
    )

    return member


# ============================================================
# UPDATE FAMILY MEMBER
# ============================================================

@transaction.atomic
def update_family_member(
    *,
    membership,
    actor,
    validated_data,
):
    """
    Update a family member's role and permissions.
    """

    if not membership:
        raise ValueError(
            "Family membership is required."
        )

    if not actor:
        raise ValueError("Actor is required.")

    membership = (
        FamilyMember.objects
        .select_for_update()
        .select_related(
            "family",
            "user",
        )
        .get(
            pk=membership.pk
        )
    )

    old_role = membership.role

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    if "role" in validated_data:

        new_role = validated_data["role"]

        if new_role not in dict(
            FamilyMember.Role.choices
        ):
            raise ValueError(
                "Invalid family member role."
            )

        if (
            membership.role
            == FamilyMember.Role.OWNER
            and new_role
            != FamilyMember.Role.OWNER
        ):
            raise ValueError(
                "The family owner cannot be demoted."
            )

        if (
            new_role == FamilyMember.Role.OWNER
            and membership.role
            != FamilyMember.Role.OWNER
        ):
            if FamilyMember.objects.filter(
                family=membership.family,
                role=FamilyMember.Role.OWNER,
            ).exclude(
                pk=membership.pk
            ).exists():
                raise ValueError(
                    "This family already has an owner."
                )

        membership.role = new_role

    # --------------------------------------------------------
    # Permissions
    # --------------------------------------------------------

    permission_fields = [
        "can_view_patient_records",
        "can_manage_appointments",
        "can_manage_medications",
        "can_manage_family_members",
        "can_manage_family_patients",
    ]

    for field in permission_fields:
        if field in validated_data:
            setattr(
                membership,
                field,
                validated_data[field],
            )

    membership.save()

    create_audit_log(
        family=membership.family,
        actor=actor,
        action=FamilyAuditLog.Action.MEMBER_UPDATED,
        metadata={
            "membership_id": membership.id,
            "member_user_id": membership.user_id,
            "old_role": old_role,
            "new_role": membership.role,
        },
    )

    return membership


# ============================================================
# REMOVE FAMILY MEMBER
# ============================================================

@transaction.atomic
def remove_family_member(
    *,
    family,
    user,
    actor,
):
    """
    Remove a non-owner family member.
    """

    if not family:
        raise ValueError("Family is required.")

    if not user:
        raise ValueError("User is required.")

    membership = (
        FamilyMember.objects
        .select_for_update()
        .filter(
            family=family,
            user=user,
        )
        .first()
    )

    if not membership:
        raise ValueError(
            "This user is not a member of the family."
        )

    if membership.role == FamilyMember.Role.OWNER:
        raise ValueError(
            "The family owner cannot be removed."
        )

    membership_id = membership.id
    member_user_id = membership.user_id
    role = membership.role

    membership.delete()

    create_audit_log(
        family=family,
        actor=actor,
        action=FamilyAuditLog.Action.MEMBER_REMOVED,
        metadata={
            "membership_id": membership_id,
            "member_user_id": member_user_id,
            "role": role,
        },
    )

    return True


# ============================================================
# GET MEMBERSHIP
# ============================================================

def get_family_membership(
    *,
    family,
    user,
):
    """
    Return a user's membership in a family.
    """

    membership = (
        FamilyMember.objects
        .select_related(
            "family",
            "user",
        )
        .filter(
            family=family,
            user=user,
        )
        .first()
    )

    if not membership:
        raise ValueError(
            "You are not a member of this family."
        )

    return membership


# ============================================================
# CHECK MEMBERSHIP
# ============================================================

def is_family_member(
    *,
    family,
    user,
):
    """
    Return True if the user belongs to the family.
    """

    if not family or not user:
        return False

    return FamilyMember.objects.filter(
        family=family,
        user=user,
    ).exists()


# ============================================================
# CHECK OWNER
# ============================================================

def is_family_owner(
    *,
    family,
    user,
):
    """
    Return True if the user is the family owner.
    """

    if not family or not user:
        return False

    return FamilyMember.objects.filter(
        family=family,
        user=user,
        role=FamilyMember.Role.OWNER,
    ).exists()


# ============================================================
# PERMISSION CHECK
# ============================================================

def member_has_permission(
    *,
    family,
    user,
    permission,
):
    """
    Check whether a family member has a specific permission.
    """

    allowed_permissions = {
        "can_view_patient_records",
        "can_manage_appointments",
        "can_manage_medications",
        "can_manage_family_members",
        "can_manage_family_patients",
    }

    if permission not in allowed_permissions:
        raise ValueError(
            "Invalid family permission."
        )

    membership = (
        FamilyMember.objects
        .filter(
            family=family,
            user=user,
        )
        .first()
    )

    if not membership:
        return False

    if membership.role == FamilyMember.Role.OWNER:
        return True

    return bool(
        getattr(
            membership,
            permission,
            False,
        )
    )