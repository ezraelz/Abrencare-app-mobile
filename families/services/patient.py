import secrets

from django.contrib.auth import get_user_model
from django.db import transaction

from patients.models import Patient

from ..models import (
    FamilyPatient,
    FamilyAuditLog,
)

from .audit import create_audit_log


User = get_user_model()


# ============================================================
# CREATE FAMILY PATIENT
# ============================================================

@transaction.atomic
def create_family_patient(
    *,
    family,
    created_by,
    validated_data,
):
    """
    Create a patient and associate the patient with a family.

    Existing users are reused by normalized email or phone.

    New patient accounts are created as pending users
    with unusable passwords.
    """

    email = (
        validated_data.get("email")
        or ""
    ).strip().lower()

    phone = (
        validated_data.get("phone_number")
        or ""
    ).strip()

    user = None

    # --------------------------------------------------------
    # Find existing user
    # --------------------------------------------------------

    if email:
        user = (
            User.objects
            .filter(email__iexact=email)
            .first()
        )

    if not user and phone:
        user = (
            User.objects
            .filter(phone_number=phone)
            .first()
        )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    if not user:

        username = (
            validated_data.get("username")
            or secrets.token_hex(8)
        )

        if User.objects.filter(
            username=username
        ).exists():
            raise ValueError(
                "This username is already in use."
            )

        user = User(
            username=username,
            email=email or None,
            phone_number=phone or None,
            first_name=validated_data[
                "first_name"
            ],
            last_name=validated_data.get(
                "last_name",
                "",
            ),
            date_of_birth=validated_data.get(
                "date_of_birth"
            ),
            account_status="pending",
        )

        user.set_unusable_password()
        user.save()

    # --------------------------------------------------------
    # Existing patient profile
    # --------------------------------------------------------

    patient = getattr(
        user,
        "patient_profile",
        None,
    )

    if not patient:
        patient = Patient.objects.create(
            user=user,
            gender=validated_data.get(
                "gender",
                "",
            ),
            blood_group=validated_data.get(
                "blood_group",
                "",
            ),
        )

    # --------------------------------------------------------
    # Prevent duplicate relationship
    # --------------------------------------------------------

    family_patient, created = (
        FamilyPatient.objects.get_or_create(
            family=family,
            patient=patient,
            defaults={
                "relationship": validated_data.get(
                    "relationship",
                    FamilyPatient.Relationship.OTHER,
                ),
                "is_primary": validated_data.get(
                    "is_primary",
                    False,
                ),
            },
        )
    )

    if not created:
        raise ValueError(
            "This patient already belongs to the family."
        )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    create_audit_log(
        family=family,
        actor=created_by,
        action=FamilyAuditLog.Action.PATIENT_CREATED,
        patient=patient,
        metadata={
            "relationship": family_patient.relationship,
            "is_primary": family_patient.is_primary,
        },
    )

    return family_patient