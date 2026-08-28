from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
)


class AppointmentListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        appointments = Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
            "doctor__specialty",
            "cancelled_by",
        )

        patient = getattr(
            request.user,
            "patient_profile",
            None,
        )

        doctor = getattr(
            request.user,
            "doctor_profile",
            None,
        )

        if patient:
            appointments = appointments.filter(
                patient=patient
            )

        elif doctor:
            appointments = appointments.filter(
                doctor=doctor
            )

        elif request.user.is_staff:
            pass

        else:
            return Response(
                {
                    "detail":
                        "You do not have access to appointments."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AppointmentSerializer(
            appointments,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):

        patient = getattr(
            request.user,
            "patient_profile",
            None,
        )

        if not patient:
            return Response(
                {
                    "detail":
                        "Only patients can create appointments."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AppointmentCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            with transaction.atomic():

                appointment = serializer.save(
                    patient=patient,
                    status=Appointment.Status.PENDING,
                )

        except IntegrityError:

            return Response(
                {
                    "detail":
                        "The selected appointment slot "
                        "is no longer available."
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            AppointmentSerializer(
                appointment
            ).data,
            status=status.HTTP_201_CREATED,
        )
    
    
class AppointmentDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        appointment = get_object_or_404(
            Appointment.objects.select_related(
                "patient__user",
                "doctor__user",
                "doctor__specialty",
                "cancelled_by",
            ),
            pk=pk,
        )

        if not self.can_access(
            request.user,
            appointment,
        ):
            return Response(
                {"detail": "You do not have access to this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AppointmentSerializer(
            appointment,
            context={"request": request},
        )

        return Response(serializer.data)

    def can_access(self, user, appointment):

        if hasattr(user, "patient_profile"):
            return appointment.patient.user_id == user.id

        if hasattr(user, "doctor_profile"):
            return appointment.doctor.user_id == user.id

        if user.is_staff:
            return True

        return False
    
class AppointmentCancelView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        appointment = get_object_or_404(
            Appointment,
            pk=pk,
        )

        is_patient = (
            hasattr(request.user, "patient_profile")
            and appointment.patient.user_id == request.user.id
        )

        is_doctor = (
            hasattr(request.user, "doctor_profile")
            and appointment.doctor.user_id == request.user.id
        )

        if not (is_patient or is_doctor or request.user.is_staff):
            return Response(
                {"detail": "You cannot cancel this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status in [
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
            Appointment.Status.NO_SHOW,
        ]:
            return Response(
                {
                    "detail":
                        "This appointment cannot be cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancelled_by = request.user
        appointment.cancellation_reason = request.data.get(
            "cancellation_reason",
            "",
        )

        appointment.save(
            update_fields=[
                "status",
                "cancelled_at",
                "cancelled_by",
                "cancellation_reason",
                "updated_at",
            ]
        )

        return Response(
            AppointmentSerializer(
                appointment,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

class AppointmentConfirmView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        appointment = get_object_or_404(
            Appointment,
            pk=pk,
        )

        allowed = (
            request.user.is_staff
            or (
                hasattr(request.user, "doctor_profile")
                and appointment.doctor.user_id == request.user.id
            )
        )

        if not allowed:
            return Response(
                {"detail": "You cannot confirm this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {
                    "detail":
                        "Only pending appointments can be confirmed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CONFIRMED
        appointment.confirmed_at = timezone.now()

        appointment.save(
            update_fields=[
                "status",
                "confirmed_at",
                "updated_at",
            ]
        )

        return Response(
            AppointmentSerializer(
                appointment,
                context={"request": request},
            ).data
        )

class AppointmentCompleteView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        appointment = get_object_or_404(
            Appointment,
            pk=pk,
        )

        allowed = (
            request.user.is_staff
            or (
                hasattr(request.user, "doctor_profile")
                and appointment.doctor.user_id == request.user.id
            )
        )

        if not allowed:
            return Response(
                {"detail": "You cannot complete this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {
                    "detail":
                        "Only confirmed appointments can be completed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.COMPLETED
        appointment.completed_at = timezone.now()

        appointment.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        return Response(
            AppointmentSerializer(
                appointment,
                context={"request": request},
            ).data
        )

class AppointmentNoShowView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        appointment = get_object_or_404(
            Appointment,
            pk=pk,
        )

        allowed = (
            request.user.is_staff
            or (
                hasattr(request.user, "doctor_profile")
                and appointment.doctor.user_id == request.user.id
            )
        )

        if not allowed:
            return Response(
                {"detail": "You cannot mark this appointment as no-show."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {
                    "detail":
                        "Only confirmed appointments can be marked as no-show."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.NO_SHOW

        appointment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            AppointmentSerializer(
                appointment,
                context={"request": request},
            ).data
        )

