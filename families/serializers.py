from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from patients.models import Patient

from .models import (
    Family,
    FamilyMember,
    FamilyPatient,
    FamilyInvitation,
    InvitationDelivery,
)

User = get_user_model()


# ============================================================
# USER / BASIC REPRESENTATION
# ============================================================

class FamilyUserSerializer(serializers.ModelSerializer):
    """
    Safe representation of a user inside the Family module.

    Sensitive authentication fields such as password are never
    exposed here.
    """

    full_name = serializers.ReadOnlyField()
    profile_picture_url = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "city",
            "profile_picture_url",
            "status",
        ]
        read_only_fields = fields


# ============================================================
# FAMILY
# ============================================================

class FamilySerializer(serializers.ModelSerializer):
    """
    Main Family representation.
    """

    created_by = FamilyUserSerializer(read_only=True)

    member_count = serializers.SerializerMethodField()
    patient_count = serializers.SerializerMethodField()

    class Meta:
        model = Family
        fields = [
            "id",
            "name",
            "created_by",
            "member_count",
            "patient_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "member_count",
            "patient_count",
            "created_at",
            "updated_at",
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_patient_count(self, obj):
        return obj.patients.count()

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Family name cannot be empty."
            )

        return value


# ============================================================
# FAMILY MEMBER
# ============================================================

class FamilyMemberSerializer(serializers.ModelSerializer):
    """
    Representation of a user belonging to a family.
    """

    user = FamilyUserSerializer(read_only=True)

    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = FamilyMember
        fields = [
            "id",
            "family",
            "user",
            "role",
            "role_display",
            "can_view_patient_records",
            "can_manage_appointments",
            "can_manage_medications",
            "can_manage_family_members",
            "can_manage_family_patients",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "family",
            "user",
            "role_display",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        role = attrs.get(
            "role",
            getattr(
                self.instance,
                "role",
                FamilyMember.Role.MEMBER,
            ),
        )

        # Owner permissions are controlled by the system.
        if role == FamilyMember.Role.OWNER:
            attrs["can_view_patient_records"] = True
            attrs["can_manage_appointments"] = True
            attrs["can_manage_medications"] = True
            attrs["can_manage_family_members"] = True
            attrs["can_manage_family_patients"] = True

        return attrs


# ============================================================
# FAMILY PATIENT
# ============================================================

class FamilyPatientSerializer(serializers.ModelSerializer):
    """
    Representation of a patient belonging to a family.
    """

    patient_id = serializers.IntegerField(
        source="patient.id",
        read_only=True,
    )

    patient_name = serializers.CharField(
        source="patient.user.full_name",
        read_only=True,
    )

    patient_user_id = serializers.IntegerField(
        source="patient.user.id",
        read_only=True,
    )

    relationship_display = serializers.CharField(
        source="get_relationship_display",
        read_only=True,
    )

    class Meta:
        model = FamilyPatient
        fields = [
            "id",
            "family",
            "patient_id",
            "patient_name",
            "patient_user_id",
            "relationship",
            "relationship_display",
            "is_primary",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "family",
            "patient_id",
            "patient_name",
            "patient_user_id",
            "relationship_display",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if (
            self.instance
            and attrs.get("is_primary") is True
            and self.instance.is_primary
        ):
            return attrs

        return attrs


# ============================================================
# PATIENT REPRESENTATION FOR FAMILY OPERATIONS
# ============================================================

class FamilyPatientDetailSerializer(serializers.ModelSerializer):
    """
    More detailed patient representation for the family dashboard.

    This intentionally does not expose medical records.
    """

    user = FamilyUserSerializer(
        source="user",
        read_only=True,
    )

    gender_display = serializers.CharField(
        source="get_gender_display",
        read_only=True,
    )

    blood_group_display = serializers.CharField(
        source="get_blood_group_display",
        read_only=True,
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "user",
            "gender",
            "gender_display",
            "blood_group",
            "blood_group_display",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


# ============================================================
# FAMILY INVITATION
# ============================================================

class FamilyInvitationSerializer(serializers.ModelSerializer):
    """
    Safe representation of a family invitation.

    The raw invitation token is NEVER returned.
    """

    invited_by = FamilyUserSerializer(
        read_only=True,
    )

    accepted_by = FamilyUserSerializer(
        read_only=True,
    )

    invitation_type_display = serializers.CharField(
        source="get_invitation_type_display",
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = FamilyInvitation
        fields = [
            "id",
            "family",
            "invited_by",
            "invitation_type",
            "invitation_type_display",
            "name",
            "email",
            "phone_number",
            "role",
            "patient",
            "status",
            "status_display",
            "expires_at",
            "is_expired",
            "accepted_by",
            "accepted_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "family",
            "invited_by",
            "status",
            "status_display",
            "is_expired",
            "accepted_by",
            "accepted_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        invitation_type = attrs.get(
            "invitation_type"
        )

        email = attrs.get(
            "email",
            getattr(self.instance, "email", ""),
        )

        phone_number = attrs.get(
            "phone_number",
            getattr(self.instance, "phone_number", ""),
        )

        patient = attrs.get(
            "patient",
            getattr(self.instance, "patient", None),
        )

        role = attrs.get(
            "role",
            getattr(self.instance, "role", ""),
        )

        # ----------------------------------------------------
        # Contact validation
        # ----------------------------------------------------

        if not email and not phone_number:
            raise serializers.ValidationError(
                {
                    "contact": (
                        "At least one of email or "
                        "phone number is required."
                    )
                }
            )

        # ----------------------------------------------------
        # PATIENT CLAIM
        # ----------------------------------------------------

        if (
            invitation_type
            == FamilyInvitation.InvitationType.PATIENT_CLAIM
        ):
            if not patient:
                raise serializers.ValidationError(
                    {
                        "patient": (
                            "A patient is required for "
                            "a patient account claim."
                        )
                    }
                )

            if role:
                raise serializers.ValidationError(
                    {
                        "role": (
                            "Role must not be provided for "
                            "a patient account claim."
                        )
                    }
                )

        # ----------------------------------------------------
        # FAMILY MEMBER
        # ----------------------------------------------------

        if (
            invitation_type
            == FamilyInvitation.InvitationType.MEMBER
        ):
            if not role:
                attrs["role"] = (
                    FamilyMember.Role.MEMBER
                )

            if patient:
                raise serializers.ValidationError(
                    {
                        "patient": (
                            "Patient must not be provided "
                            "for a family member invitation."
                        )
                    }
                )

        # ----------------------------------------------------
        # Validate expiration
        # ----------------------------------------------------

        expires_at = attrs.get(
            "expires_at",
            getattr(
                self.instance,
                "expires_at",
                None,
            ),
        )

        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError(
                {
                    "expires_at": (
                        "Invitation expiration must be "
                        "in the future."
                    )
                }
            )

        return attrs


# ============================================================
# CREATE FAMILY MEMBER INVITATION
# ============================================================

class CreateFamilyMemberInvitationSerializer(
    serializers.Serializer
):
    """
    Input serializer used when a family owner invites
    another person.

    This serializer does not create the invitation itself.
    The service layer should handle token generation,
    invalidating previous invitations and notification
    delivery.
    """

    name = serializers.CharField(
        max_length=150,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
    )

    role = serializers.ChoiceField(
        choices=[
            (
                FamilyMember.Role.MEMBER,
                FamilyMember.Role.MEMBER.label,
            ),
            (
                FamilyMember.Role.CAREGIVER,
                FamilyMember.Role.CAREGIVER.label,
            ),
        ],
        default=FamilyMember.Role.MEMBER,
    )

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Name is required."
            )

        return value

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone_number")

        if not email and not phone:
            raise serializers.ValidationError(
                {
                    "contact": (
                        "Provide either an email address "
                        "or phone number."
                    )
                }
            )

        return attrs


# ============================================================
# CREATE FAMILY PATIENT
# ============================================================

class CreateFamilyPatientSerializer(
    serializers.Serializer
):
    """
    Creates a family patient.

    The actual creation of User + Patient +
    FamilyPatient belongs in the service layer.
    """

    first_name = serializers.CharField(
        max_length=30,
    )

    last_name = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone_number = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
    )

    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
    )

    gender = serializers.ChoiceField(
        choices=Patient.Gender.choices,
        required=False,
        allow_blank=True,
    )

    blood_group = serializers.ChoiceField(
        choices=Patient.BloodGroup.choices,
        required=False,
        allow_blank=True,
    )

    relationship = serializers.ChoiceField(
        choices=FamilyPatient.Relationship.choices,
        default=FamilyPatient.Relationship.OTHER,
    )

    is_primary = serializers.BooleanField(
        default=False,
    )

    def validate_first_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "First name is required."
            )

        return value

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone_number")

        if not email and not phone:
            raise serializers.ValidationError(
                {
                    "contact": (
                        "Provide either an email address "
                        "or phone number for the patient."
                    )
                }
            )

        return attrs


# ============================================================
# PATIENT CLAIM INVITATION
# ============================================================

class CreatePatientClaimInvitationSerializer(
    serializers.Serializer
):
    """
    Creates an invitation allowing an existing pending
    patient to claim their account.
    """

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone_number")

        if not email and not phone:
            raise serializers.ValidationError(
                {
                    "contact": (
                        "Provide either an email address "
                        "or phone number."
                    )
                }
            )

        return attrs


# ============================================================
# INVITATION ACCEPTANCE
# ============================================================

class AcceptInvitationSerializer(
    serializers.Serializer
):
    """
    Used when an existing authenticated user accepts
    an invitation.

    No password is accepted here.
    """

    confirm = serializers.BooleanField(
        default=True,
    )

    def validate_confirm(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "You must confirm acceptance of the invitation."
            )

        return value


# ============================================================
# COMPLETE INVITATION REGISTRATION
# ============================================================

class CompleteInvitationRegistrationSerializer(
    serializers.Serializer
):
    """
    Used after invitation/contact verification when
    the invited person does not yet have an account.
    """

    first_name = serializers.CharField(
        max_length=30,
    )

    last_name = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )

    username = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    password_confirmation = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {
                    "password_confirmation": (
                        "Passwords do not match."
                    )
                }
            )

        return attrs


# ============================================================
# INVITATION DELIVERY
# ============================================================

class InvitationDeliverySerializer(
    serializers.ModelSerializer
):
    """
    Delivery history representation.

    Provider information is visible for administration
    but the actual invitation token is never exposed.
    """

    channel_display = serializers.CharField(
        source="get_channel_display",
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = InvitationDelivery
        fields = [
            "id",
            "invitation",
            "channel",
            "channel_display",
            "destination",
            "status",
            "status_display",
            "provider_message_id",
            "error_message",
            "sent_at",
            "created_at",
        ]

        read_only_fields = fields


class VerifyInvitationOTPSerializer(serializers.Serializer):
    """
    Verify an OTP previously sent for an invitation.
    """

    otp = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=10,
        trim_whitespace=True,
    )

    def validate_otp(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only digits."
            )

        return value

    