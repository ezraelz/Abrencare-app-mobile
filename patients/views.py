from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Patient,
    EmergencyContact,
    MedicalRecord,
    MedicalDocument,
)

from .serializers import (
    PatientSerializer,
    EmergencyContactSerializer,
    MedicalRecordSerializer,
    MedicalDocumentSerializer,
)

from .permissions import (
    IsPatient,
    IsPatientOwner,
    IsEmergencyContactOwner,
    IsMedicalDocumentOwner,
)


# ==========================================================
# PATIENT PROFILE
# ==========================================================

class PatientMeView(APIView):
    """
    Current authenticated user's patient profile.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):

        patient = get_object_or_404(
            Patient.objects.select_related("user"),
            user=request.user,
        )

        serializer = PatientSerializer(
            patient,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Create the authenticated user's Patient profile.

        The user is ALWAYS derived from request.user.
        """

        if not request.user.is_active:
            return Response(
                {
                    "detail":
                        "Your account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if Patient.objects.filter(
            user=request.user
        ).exists():
            return Response(
                {
                    "detail":
                        "A patient profile already exists "
                        "for this account."
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = PatientSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        patient = serializer.save(
            user=request.user
        )

        return Response(
            PatientSerializer(
                patient,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):

        patient = get_object_or_404(
            Patient.objects.select_related("user"),
            user=request.user,
        )

        serializer = PatientSerializer(
            patient,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        patient = serializer.save()

        return Response(
            PatientSerializer(
                patient,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )


# ==========================================================
# PATIENT DETAIL
# ==========================================================

class PatientDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatientOwner,
    ]

    def get(self, request, pk):

        patient = get_object_or_404(
            Patient.objects.select_related("user"),
            pk=pk,
        )

        self.check_object_permissions(
            request,
            patient,
        )

        serializer = PatientSerializer(
            patient,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):

        patient = get_object_or_404(
            Patient.objects.select_related("user"),
            pk=pk,
        )

        self.check_object_permissions(
            request,
            patient,
        )

        serializer = PatientSerializer(
            patient,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        patient = serializer.save()

        return Response(
            PatientSerializer(
                patient,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        return Response(
            {
                "detail":
                    "Patient profiles cannot be deleted. "
                    "Deactivate the account instead."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


# ==========================================================
# ACCOUNT DEACTIVATION
# ==========================================================

class PatientDeactivateAccountView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def post(self, request):

        user = request.user

        if not user.is_active:
            return Response(
                {
                    "detail":
                        "Your account is already inactive."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = False

        user.save(
            update_fields=["is_active"]
        )

        return Response(
            {
                "detail":
                    "Your account has been deactivated."
            },
            status=status.HTTP_200_OK,
        )


# ==========================================================
# EMERGENCY CONTACTS
# ==========================================================

class EmergencyContactListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get(self, request):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        contacts = patient.emergency_contacts.all()

        serializer = EmergencyContactSerializer(
            contacts,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        serializer = EmergencyContactSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        contact = serializer.save(
            patient=patient
        )

        return Response(
            EmergencyContactSerializer(contact).data,
            status=status.HTTP_201_CREATED,
        )


class EmergencyContactDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get(self, request, pk):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        contact = get_object_or_404(
            EmergencyContact,
            pk=pk,
            patient=patient,
        )

        return Response(
            EmergencyContactSerializer(contact).data
        )

    def patch(self, request, pk):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        contact = get_object_or_404(
            EmergencyContact,
            pk=pk,
            patient=patient,
        )

        serializer = EmergencyContactSerializer(
            contact,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        contact = serializer.save()

        return Response(
            EmergencyContactSerializer(contact).data
        )

    def delete(self, request, pk):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        contact = get_object_or_404(
            EmergencyContact,
            pk=pk,
            patient=patient,
        )

        contact.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
# ==========================================================
# MEDICAL RECORDS
# ==========================================================

class PatientMedicalRecordListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get(self, request):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        records = (
            MedicalRecord.objects
            .filter(patient=patient)
            .select_related(
                "patient__user",
                "doctor__user",
            )
        )

        serializer = MedicalRecordSerializer(
            records,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class PatientMedicalRecordDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get(self, request, pk):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        record = get_object_or_404(
            MedicalRecord.objects.select_related(
                "patient__user",
                "doctor__user",
            ),
            pk=pk,
            patient=patient,
        )

        serializer = MedicalRecordSerializer(
            record
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, pk):

        return Response(
            {
                "detail":
                    "Patients cannot create or modify "
                    "medical records."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def delete(self, request, pk):

        return Response(
            {
                "detail":
                    "Patients cannot delete medical records."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


# ==========================================================
# MEDICAL DOCUMENTS
# ==========================================================

class PatientMedicalDocumentListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get(self, request):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        documents = (
            MedicalDocument.objects
            .filter(patient=patient)
            .select_related(
                "patient__user",
                "uploaded_by",
            )
        )

        serializer = MedicalDocumentSerializer(
            documents,
            many=True,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        serializer = MedicalDocumentSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        document = serializer.save(
            patient=patient,
            uploaded_by=request.user,
        )

        return Response(
            MedicalDocumentSerializer(
                document,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PatientMedicalDocumentDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsMedicalDocumentOwner,
    ]

    def get(self, request, pk):

        document = get_object_or_404(
            MedicalDocument.objects.select_related(
                "patient__user",
                "uploaded_by",
            ),
            pk=pk,
        )

        self.check_object_permissions(
            request,
            document,
        )

        serializer = MedicalDocumentSerializer(
            document,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        document = get_object_or_404(
            MedicalDocument,
            pk=pk,
        )

        self.check_object_permissions(
            request,
            document,
        )

        document.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class PatientMedicalDocumentReplaceView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def post(self, request, pk):

        patient = get_object_or_404(
            Patient,
            user=request.user,
        )

        old_document = get_object_or_404(
            MedicalDocument,
            pk=pk,
            patient=patient,
            is_current=True,
        )

        serializer = MedicalDocumentSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        with transaction.atomic():

            old_document.is_current = False

            old_document.save(
                update_fields=["is_current"]
            )

            new_document = serializer.save(
                patient=patient,
                uploaded_by=request.user,
                version=old_document.version + 1,
                is_current=True,
                replaced_document=old_document,
            )

        return Response(
            MedicalDocumentSerializer(
                new_document,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )
    