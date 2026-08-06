from rest_framework import serializers
from .models import (
    Specialty,
    Doctor,
    Qualification,
    DoctorAvailability,
)
from roles.models import Role
from accounts.models import User


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = "__all__"


class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = "__all__"
        read_only_fields = ("created_at",)


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = "__all__"
        read_only_fields = ("created_at",)


class DoctorSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    specialty_name = serializers.CharField(
        source="specialty.name",
        read_only=True
    )

    qualifications = QualificationSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Doctor
        fields = [
            "id",
            "user",
            "user_name",
            "specialization",
            "license_number",
            "years_of_experience",
            "consultation_fee",
            "bio",
            "verified",
            "specialty",
            "specialty_name",
            "qualifications",
            "created_at",
        ]
        read_only_fields = ("created_at",)

class DoctorRegisterSerializer(serializers.ModelSerializer):
    doctor_details = DoctorSerializer(required=False)
    class Meta:
        model = Doctor
        fields = [
            "user",
            "user_name",
            "specialization",
            "license_number",
            "years_of_experience",
            "consultation_fee",
            "bio",
            "verified",
            "specialty",
            "specialty_name",
            "qualifications",
        ]

    def create(self, validated_data):
        doctor_details_data = validated_data.pop('doctor_details', None)
        password = validated_data.pop('password')

        role,_= Role.objects.get_or_create(role_name='doctor')

        profile = User.objects.create(**validated_data)
        profile.set_password(password)
        profile.role = role
        profile.save()

        if doctor_details_data: 
            Doctor.objects.create(
                profile=profile,
                **doctor_details_data
            )
        return profile
    