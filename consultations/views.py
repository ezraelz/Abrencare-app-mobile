from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from doctors.models import Doctor, Specialty

from .models import Consultation
from .permissions import IsDoctorUser, IsPatientUser
from .serializers import (
    ConsultationBookingSerializer,
    ConsultationCancelSerializer,
    ConsultationDoctorSerializer,
    ConsultationSerializer,
    ConsultationSlotSerializer,
    PrescriptionCreateSerializer,
    PrescriptionSerializer,
    SpecialtySerializer,
)
from .services.services import (
    ACTIVE_APPOINTMENT_STATUSES,
    book_consultation,
    cancel_consultation,
    complete_consultation,
    create_prescription,
    start_consultation,
)


# ============================================================
# SPECIALTIES
# ============================================================

class SpecialtyListView(APIView):
    """Return active specialties available for digital consultation."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        specialties = Specialty.objects.filter(is_active=True)
        serializer = SpecialtySerializer(specialties, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# DOCTORS
# ============================================================

class ConsultationDoctorListView(APIView):
    """
    Return approved doctors.
    Optional: ?specialty=<specialty_id>
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        specialty_id = request.query_params.get("specialty")

        queryset = (
            Doctor.objects
            .filter(approval_status=Doctor.ApprovalStatus.APPROVED, specialty__is_active=True)
            .select_related("user", "specialty")
        )

        if specialty_id:
            queryset = queryset.filter(specialty_id=specialty_id)

        serializer = ConsultationDoctorSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# AVAILABILITY
# ============================================================

class ConsultationAvailabilityView(APIView):
    """
    Return available consultation slots for a doctor/date.

    Example:
        GET /api/consultations/availability/?doctor=12&date=2026-08-30
    """

    permission_classes = [IsAuthenticated]
    SLOT_INTERVAL_MINUTES = 30

    def get(self, request):
        doctor_id = request.query_params.get("doctor")
        date_string = request.query_params.get("date")

        if not doctor_id:
            return Response({"doctor": "This parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not date_string:
            return Response({"date": "This parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor_id = int(doctor_id)
        except ValueError:
            return Response({"doctor": "Must be a valid integer id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appointment_date = datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError:
            return Response({"date": "Use YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST)

        if appointment_date < timezone.localdate():
            return Response({"date": "Date cannot be in the past."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = (
                Doctor.objects
                .select_related("user", "specialty")
                .get(pk=doctor_id, approval_status=Doctor.ApprovalStatus.APPROVED)
            )
        except Doctor.DoesNotExist:
            return Response({"doctor": "Doctor not found or unavailable."}, status=status.HTTP_404_NOT_FOUND)

        weekday = appointment_date.strftime("%A").lower()

        availability_windows = (
            doctor.availability
            .filter(day=weekday, is_available=True)
            .order_by("start_time")
        )

        active_appointments = (
            doctor.appointments
            .filter(appointment_date=appointment_date, status__in=ACTIVE_APPOINTMENT_STATUSES)
            .order_by("appointment_time")
        )

        # Pre-compute booked intervals once instead of re-deriving them per slot.
        booked_intervals = [
            (
                datetime.combine(appointment_date, a.appointment_time),
                datetime.combine(appointment_date, a.appointment_time) + timedelta(minutes=a.duration_minutes),
            )
            for a in active_appointments
        ]

        duration = doctor.consultation_duration
        slots = []

        for window in availability_windows:
            current = datetime.combine(appointment_date, window.start_time)
            window_end = datetime.combine(appointment_date, window.end_time)

            while current + timedelta(minutes=duration) <= window_end:
                slot_start = current
                slot_end = current + timedelta(minutes=duration)

                available = not any(
                    slot_start < booked_end and slot_end > booked_start
                    for booked_start, booked_end in booked_intervals
                )

                slots.append({"time": current.time(), "available": available})
                current += timedelta(minutes=self.SLOT_INTERVAL_MINUTES)

        serializer = ConsultationSlotSerializer(slots, many=True)

        return Response(
            {
                "doctor": {
                    "id": doctor.id,
                    "name": doctor.user.full_name,
                    "specialty": doctor.specialty.name,
                },
                "date": appointment_date,
                "duration_minutes": duration,
                "slots": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# BOOK CONSULTATION
# ============================================================

class ConsultationBookingView(APIView):
    """Book a digital consultation for the authenticated patient."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConsultationBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doctor = get_object_or_404(Doctor, pk=request.data["doctor"])

        try:
            consultation = book_consultation(
                user=request.user,
                doctor=doctor,
                appointment_date=serializer.validated_data["appointment_date"],
                appointment_time=serializer.validated_data["appointment_time"],
            )

        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = ConsultationSerializer(consultation)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ============================================================
# MY CONSULTATIONS
# ============================================================

class MyConsultationsView(APIView):
    """Return consultations belonging to the authenticated patient."""

    permission_classes = [IsAuthenticated, IsPatientUser]

    def get(self, request):
        consultations = (
            Consultation.objects
            .select_related(
                "appointment",
                "appointment__patient",
                "appointment__doctor",
                "appointment__doctor__user",
                "appointment__doctor__specialty",
            )
            .filter(appointment__patient=request.user.patient_profile)
            .order_by("-appointment__appointment_date", "-appointment__appointment_time")
        )

        serializer = ConsultationSerializer(consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# CONSULTATION DETAIL
# ============================================================

class ConsultationDetailView(APIView):
    """Return one consultation belonging to the authenticated patient."""

    permission_classes = [IsAuthenticated, IsPatientUser]

    def get(self, request, pk):
        consultation = (
            Consultation.objects
            .select_related(
                "appointment",
                "appointment__patient",
                "appointment__doctor",
                "appointment__doctor__user",
                "appointment__doctor__specialty",
            )
            .filter(pk=pk, appointment__patient=request.user.patient_profile)
            .first()
        )

        if not consultation:
            return Response({"detail": "Consultation not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConsultationSerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# CANCEL
# ============================================================

class ConsultationCancelView(APIView):
    """Cancel a consultation belonging to the authenticated patient."""

    permission_classes = [IsAuthenticated, IsPatientUser]

    def post(self, request, pk):
        input_serializer = ConsultationCancelSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            consultation = (
                Consultation.objects
                .select_related("appointment", "appointment__patient")
                .get(pk=pk, appointment__patient=request.user.patient_profile)
            )
        except Consultation.DoesNotExist:
            return Response({"detail": "Consultation not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            consultation = cancel_consultation(
                consultation=consultation,
                user=request.user,
                reason=input_serializer.validated_data["reason"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ConsultationSerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# START CONSULTATION
# ============================================================

class ConsultationStartView(APIView):
    """Start a consultation. Restricted to the assigned doctor."""

    permission_classes = [IsAuthenticated, IsDoctorUser]

    def post(self, request, pk):
        try:
            consultation = (
                Consultation.objects
                .select_related("appointment", "appointment__doctor")
                .get(pk=pk, appointment__doctor=request.user.doctor)
            )
        except Consultation.DoesNotExist:
            return Response({"detail": "Consultation not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            consultation = start_consultation(consultation=consultation, user=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ConsultationSerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# COMPLETE CONSULTATION
# ============================================================

class ConsultationCompleteView(APIView):
    """Complete a consultation. Restricted to the assigned doctor."""

    permission_classes = [IsAuthenticated, IsDoctorUser]

    def post(self, request, pk):
        try:
            consultation = (
                Consultation.objects
                .select_related("appointment", "appointment__doctor")
                .get(pk=pk, appointment__doctor=request.user.doctor)
            )
        except Consultation.DoesNotExist:
            return Response({"detail": "Consultation not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            consultation = complete_consultation(consultation=consultation, user=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ConsultationSerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# CREATE PRESCRIPTION
# ============================================================

class PrescriptionCreateView(APIView):
    """Create a prescription for a consultation. Restricted to the assigned doctor."""

    permission_classes = [IsAuthenticated, IsDoctorUser]

    def post(self, request, pk):
        try:
            consultation = (
                Consultation.objects
                .select_related("appointment", "appointment__doctor")
                .get(pk=pk, appointment__doctor=request.user.doctor)
            )
        except Consultation.DoesNotExist:
            return Response({"detail": "Consultation not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PrescriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            prescription = create_prescription(
                consultation=consultation,
                doctor=request.user.doctor,
                data=serializer.validated_data,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = PrescriptionSerializer(prescription)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    