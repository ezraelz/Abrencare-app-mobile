from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from .models import (
    Doctor,
    Specialty,
    Qualification,
    DoctorAvailability,
)


User = get_user_model()


# ============================================================
# SPECIALTY
# ============================================================

class SpecialtySerializer(serializers.ModelSerializer):

    class Meta:
        model = Specialty
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Specialty name cannot be empty."
            )

        queryset = Specialty.objects.filter(
            name__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A specialty with this name already exists."
            )

        return value


# ============================================================
# QUALIFICATION
# ============================================================

class QualificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Qualification

        fields = [
            "id",
            "doctor",
            "degree",
            "institution",
            "year_of_completion",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "doctor",
            "created_at",
            "updated_at",
        ]

    def validate_year_of_completion(self, value):

        current_year = timezone.now().year

        if value > current_year:
            raise serializers.ValidationError(
                "Year of completion cannot be in the future."
            )

        if value < 1900:
            raise serializers.ValidationError(
                "Please provide a valid year of completion."
            )

        return value

    def validate_degree(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Degree cannot be empty."
            )

        return value

    def validate_institution(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Institution cannot be empty."
            )

        return value


# ============================================================
# DOCTOR AVAILABILITY
# ============================================================

class DoctorAvailabilitySerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = DoctorAvailability

        fields = [
            "id",
            "doctor",
            "day",
            "start_time",
            "end_time",
            "is_available",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "doctor",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        start_time = attrs.get(
            "start_time",
            getattr(
                self.instance,
                "start_time",
                None,
            ),
        )

        end_time = attrs.get(
            "end_time",
            getattr(
                self.instance,
                "end_time",
                None,
            ),
        )

        if start_time and end_time:

            if start_time >= end_time:
                raise serializers.ValidationError({
                    "end_time":
                        "End time must be later than start time."
                })

        doctor = self.context.get("doctor")

        if not doctor and self.instance:
            doctor = self.instance.doctor

        day = attrs.get(
            "day",
            getattr(
                self.instance,
                "day",
                None,
            ),
        )

        if doctor and day and start_time and end_time:

            queryset = DoctorAvailability.objects.filter(
                doctor=doctor,
                day=day,
            ).exclude(
                is_available=False
            )

            if self.instance:
                queryset = queryset.exclude(
                    pk=self.instance.pk
                )

            overlapping = queryset.filter(
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if overlapping.exists():
                raise serializers.ValidationError(
                    "This availability period overlaps "
                    "with an existing availability period."
                )

        return attrs


# ============================================================
# USER SUMMARY
# ============================================================

class DoctorUserSerializer(
    serializers.ModelSerializer
):

    full_name = serializers.ReadOnlyField()

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
            "profile_picture_url",
        ]

        read_only_fields = fields


# ============================================================
# DOCTOR LIST
# ============================================================

class DoctorListSerializer(serializers.ModelSerializer):

    full_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    specialty_name = serializers.CharField(
        source="specialty.name",
        read_only=True,
    )

    class Meta:
        model = Doctor

        fields = [
            "id",
            "full_name",
            "email",
            "specialty",
            "specialty_name",
            "license_number",
            "years_of_experience",
            "consultation_fee",
            "consultation_duration",
            "bio",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


# ============================================================
# DOCTOR DETAIL
# ============================================================

class DoctorDetailSerializer(
    serializers.ModelSerializer
):

    user = DoctorUserSerializer(
        read_only=True
    )

    specialty_name = serializers.CharField(
        source="specialty.name",
        read_only=True,
    )

    qualifications = QualificationSerializer(
        many=True,
        read_only=True,
    )

    availability = DoctorAvailabilitySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Doctor

        fields = [
            "id",
            "user",
            "specialty",
            "specialty_name",
            "license_number",
            "years_of_experience",
            "consultation_fee",
            "consultation_duration",
            "bio",
            "qualifications",
            "availability",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "qualifications",
            "availability",
            "created_at",
            "updated_at",
        ]


# ============================================================
# DOCTOR CREATE
# ============================================================

class DoctorCreateSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Doctor

        fields = [
            "specialty",
            "license_number",
            "years_of_experience",
            "consultation_fee",
            "consultation_duration",
            "bio",
        ]

    def validate_license_number(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "License number is required."
            )

        queryset = Doctor.objects.filter(
            license_number__iexact=value
        )

        if queryset.exists():
            raise serializers.ValidationError(
                "A doctor with this license number already exists."
            )

        return value

    def validate_years_of_experience(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Years of experience cannot be negative."
            )

        return value

    def validate_consultation_fee(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Consultation fee cannot be negative."
            )

        return value

    def validate_consultation_duration(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Consultation duration must be greater than zero."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):

        user = self.context["request"].user

        if hasattr(user, "doctor"):
            raise serializers.ValidationError(
                "This user already has a doctor profile."
            )

        doctor = Doctor.objects.create(
            user=user,
            approval_status=Doctor.ApprovalStatus.PENDING,
            **validated_data,
        )

        return doctor


# ============================================================
# DOCTOR UPDATE
# ============================================================

class DoctorUpdateSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Doctor

        fields = [
            "specialty",
            "license_number",
            "years_of_experience",
            "consultation_fee",
            "consultation_duration",
            "bio",
        ]

    def validate_license_number(self, value):

        value = value.strip()

        queryset = Doctor.objects.filter(
            license_number__iexact=value
        ).exclude(
            pk=self.instance.pk
        )

        if queryset.exists():
            raise serializers.ValidationError(
                "A doctor with this license number already exists."
            )

        return value

    def validate_consultation_fee(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Consultation fee cannot be negative."
            )

        return value

    def validate_consultation_duration(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Consultation duration must be greater than zero."
            )

        return value
    