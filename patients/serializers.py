from django.db import transaction
from rest_framework import serializers

from .models import (
    Patient,
    EmergencyContact,
    MedicalRecord,
    MedicalDocument,
)


class PatientSerializer(serializers.ModelSerializer):
    """
    Patient profile serializer.

    The User model remains the source of truth for:
    - name
    - email
    - phone
    - address
    - city
    - postal code
    - date of birth
    - profile picture
    """

    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True,
    )

    full_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )

    date_of_birth = serializers.DateField(
        source="user.date_of_birth",
        read_only=True,
    )

    address = serializers.CharField(
        source="user.address",
        read_only=True,
    )

    city = serializers.CharField(
        source="user.city",
        read_only=True,
    )

    postal_code = serializers.CharField(
        source="user.postal_code",
        read_only=True,
    )

    profile_picture_url = serializers.CharField(
        source="user.profile_picture_url",
        read_only=True,
    )

    account_status = serializers.CharField(
        source="user.status",
        read_only=True,
    )

    class Meta:
        model = Patient

        fields = [
            "id",
            "user_id",
            "full_name",
            "email",
            "phone_number",
            "date_of_birth",
            "address",
            "city",
            "postal_code",
            "profile_picture_url",
            "account_status",
            "gender",
            "blood_group",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_id",
            "full_name",
            "email",
            "phone_number",
            "date_of_birth",
            "address",
            "city",
            "postal_code",
            "profile_picture_url",
            "account_status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context.get("request")

        if request and request.user:
            if not request.user.is_authenticated:
                raise serializers.ValidationError(
                    "Authentication is required."
                )

        return attrs


class EmergencyContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmergencyContact

        fields = [
            "id",
            "patient",
            "name",
            "relationship",
            "phone_number",
            "alternative_phone",
            "is_primary",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "created_at",
            "updated_at",
        ]

    def validate_phone_number(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Phone number is required."
            )

        return value

    def validate(self, attrs):
        phone = attrs.get("phone_number")
        alternative = attrs.get("alternative_phone")

        if phone and alternative and phone == alternative:
            raise serializers.ValidationError(
                {
                    "alternative_phone":
                        "Alternative phone must be different from "
                        "the primary phone."
                }
            )

        return attrs


class MedicalRecordSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source="patient.user.full_name",
        read_only=True,
    )

    doctor_name = serializers.CharField(
        source="doctor.user.full_name",
        read_only=True,
    )

    class Meta:
        model = MedicalRecord

        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "diagnosis",
            "treatment",
            "allergies",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "diagnosis",
            "treatment",
            "allergies",
            "notes",
            "created_at",
            "updated_at",
        ]


class MedicalDocumentSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source="patient.user.full_name",
        read_only=True,
    )

    uploaded_by_name = serializers.CharField(
        source="uploaded_by.full_name",
        read_only=True,
    )

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MedicalDocument

        fields = [
            "id",
            "patient",
            "patient_name",
            "uploaded_by",
            "uploaded_by_name",
            "file",
            "file_url",
            "description",
            "version",
            "is_current",
            "replaced_document",
            "uploaded_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_name",
            "uploaded_by",
            "uploaded_by_name",
            "file_url",
            "version",
            "is_current",
            "replaced_document",
            "uploaded_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")

        if not obj.file:
            return None

        if request:
            return request.build_absolute_uri(
                obj.file.url
            )

        return obj.file.url

    def validate_file(self, value):

        max_size = 10 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "File size cannot exceed 10 MB."
            )

        allowed_extensions = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
        }

        filename = value.name.lower()

        if not any(
            filename.endswith(ext)
            for ext in allowed_extensions
        ):
            raise serializers.ValidationError(
                "Unsupported file type. "
                "Allowed types are PDF, JPG, JPEG and PNG."
            )

        return value
    