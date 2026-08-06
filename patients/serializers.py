from rest_framework import serializers
from .models import (
    Patient,
    MedicalRecord,
    MedicalDocument,
)
from roles.models import Role
from accounts.models import User

class PatientSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "user",
            "user_name",
            "date_of_birth",
            "gender",
            "blood_group",
            "emergency_contact",
            "address",
        ]


class PatientRegisterSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(required=False)
    class Meta:
        model = Patient
        fields = [
            "id",
            "user",
            "date_of_birth",
            "gender",
            "blood_group",
            "emergency_contact",
            "address",
        ]

    def create(self, validated_data):
        patient_details_data = validated_data.pop('patient_details', None)
        password = validated_data.pop('password')

        role,_= Role.objects.get_or_create(role_name='patient')

        profile = User.objects.create(**validated_data)
        profile.set_password(password)
        profile.role = role
        profile.save()

        if patient_details_data: 
            Patient.objects.create(
                profile=profile,
                **patient_details_data
            )
        return profile


class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="patient.user.get_full_name",
        read_only=True
    )

    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name",
        read_only=True
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
            "created_at",
        ]
        read_only_fields = ("created_at",)


class MedicalDocumentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="patient.user.get_full_name",
        read_only=True
    )

    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name",
        read_only=True
    )

    class Meta:
        model = MedicalDocument
        fields = [
            "id",
            "patient",
            "patient_name",
            "uploaded_by",
            "uploaded_by_name",
            "file",
            "description",
            "uploaded_at",
        ]
        read_only_fields = ("uploaded_at",)
        