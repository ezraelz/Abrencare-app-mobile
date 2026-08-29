from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment, AppointmentCheckIn
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentCancelSerializer,
    AppointmentRescheduleSerializer,
)
from .services.appointment_notification_service import (
    AppointmentNotificationService,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class AppointmentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def get_user_patient(user):
    return getattr(user, "patient_profile", None)


def get_user_doctor(user):
    return getattr(user, "doctor_profile", None)


def user_can_access_appointment(user, appointment) -> bool:
    if user.is_staff:
        return True
    patient = get_user_patient(user)
    if patient and appointment.patient_id == patient.id:
        return True
    doctor = get_user_doctor(user)
    if doctor and appointment.doctor_id == doctor.id:
        return True
    return False


def user_can_manage_appointment(user, appointment) -> bool:
    """Doctor of the appointment or staff."""
    if user.is_staff:
        return True
    doctor = get_user_doctor(user)
    return bool(doctor and appointment.doctor_id == doctor.id)


def get_base_queryset():
    return Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
        "doctor__specialty",
        "cancelled_by",
    ).prefetch_related(
        Prefetch(
            "check_in",
            queryset=AppointmentCheckIn.objects.only(
                "checked_in_at",
                "latitude",
                "longitude",
                "gps_verified",
                "created_at",
            ),
        )
    )


# ---------------------------------------------------------------------------
# List + Create
# ---------------------------------------------------------------------------

class AppointmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AppointmentPagination

    def get_queryset(self, request):
        qs = get_base_queryset()

        patient = get_user_patient(request.user)
        doctor = get_user_doctor(request.user)

        if patient:
            qs = qs.filter(patient=patient)
        elif doctor:
            qs = qs.filter(doctor=doctor)
        elif request.user.is_staff:
            pass  # staff sees everything
        else:
            return Appointment.objects.none()

        # ----- Filtering -----
        params = request.query_params

        status_param = params.get("status")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        date = params.get("date")
        if date:
            qs = qs.filter(appointment_date=date)

        date_from = params.get("from")
        if date_from:
            qs = qs.filter(appointment_date__gte=date_from)

        date_to = params.get("to")
        if date_to:
            qs = qs.filter(appointment_date__lte=date_to)

        upcoming = params.get("upcoming")
        if upcoming and upcoming.lower() in ("1", "true", "yes"):
            today = timezone.localdate()
            now_time = timezone.localtime().time()
            qs = qs.filter(
                Q(appointment_date__gt=today)
                | Q(appointment_date=today, appointment_time__gte=now_time)
            ).exclude(
                status__in=[
                    Appointment.Status.CANCELLED,
                    Appointment.Status.COMPLETED,
                    Appointment.Status.NO_SHOW,
                ]
            )

        return qs

    def get(self, request):
        qs = self.get_queryset(request)

        if not (
            get_user_patient(request.user)
            or get_user_doctor(request.user)
            or request.user.is_staff
        ):
            return Response(
                {"detail": "You do not have access to appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = AppointmentSerializer(
            page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        patient = get_user_patient(request.user)
        if not patient:
            return Response(
                {"detail": "Only patients can create appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AppointmentCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                appointment = serializer.save(
                    patient=patient,
                    status=Appointment.Status.PENDING,
                )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "The selected appointment slot is no longer available."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Notification AFTER successful commit
        AppointmentNotificationService.notify_created(appointment)

        # Re-fetch with full relations for the response
        appointment = get_base_queryset().get(pk=appointment.pk)
        return Response(
            AppointmentSerializer(
                appointment, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

class AppointmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        appointment = get_object_or_404(get_base_queryset(), pk=pk)

        if not user_can_access_appointment(request.user, appointment):
            return Response(
                {"detail": "You do not have access to this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AppointmentSerializer(
            appointment, context={"request": request}
        )
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

class AppointmentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(get_base_queryset(), pk=pk)

        if not user_can_access_appointment(request.user, appointment):
            return Response(
                {"detail": "You cannot cancel this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        is_patient = (
            get_user_patient(request.user)
            and appointment.patient_id == get_user_patient(request.user).id
        )
        is_doctor = (
            get_user_doctor(request.user)
            and appointment.doctor_id == get_user_doctor(request.user).id
        )
        if not (is_patient or is_doctor or request.user.is_staff):
            return Response(
                {"detail": "You cannot cancel this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status in (
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
            Appointment.Status.NO_SHOW,
        ):
            return Response(
                {"detail": "This appointment cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cancel_serializer = AppointmentCancelSerializer(data=request.data)
        cancel_serializer.is_valid(raise_exception=True)

        appointment.status = Appointment.Status.CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancelled_by = request.user
        appointment.cancellation_reason = cancel_serializer.validated_data.get(
            "cancellation_reason", ""
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

        # Notification AFTER successful save
        AppointmentNotificationService.notify_cancelled(
            appointment, cancelled_by=request.user
        )

        return Response(
            AppointmentSerializer(
                appointment, context={"request": request}
            ).data
        )


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------

class AppointmentConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(get_base_queryset(), pk=pk)

        if not user_can_manage_appointment(request.user, appointment):
            return Response(
                {"detail": "You cannot confirm this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {"detail": "Only pending appointments can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CONFIRMED
        appointment.confirmed_at = timezone.now()
        appointment.save(
            update_fields=["status", "confirmed_at", "updated_at"]
        )

        # Notification AFTER successful save
        AppointmentNotificationService.notify_confirmed(appointment)

        return Response(
            AppointmentSerializer(
                appointment, context={"request": request}
            ).data
        )


# ---------------------------------------------------------------------------
# Complete
# ---------------------------------------------------------------------------

class AppointmentCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(get_base_queryset(), pk=pk)

        if not user_can_manage_appointment(request.user, appointment):
            return Response(
                {"detail": "You cannot complete this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {"detail": "Only confirmed appointments can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.COMPLETED
        appointment.completed_at = timezone.now()
        appointment.save(
            update_fields=["status", "completed_at", "updated_at"]
        )

        # Notification AFTER successful save
        AppointmentNotificationService.notify_completed(appointment)

        return Response(
            AppointmentSerializer(
                appointment, context={"request": request}
            ).data
        )


# ---------------------------------------------------------------------------
# No-Show
# ---------------------------------------------------------------------------

class AppointmentNoShowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(get_base_queryset(), pk=pk)

        if not user_can_manage_appointment(request.user, appointment):
            return Response(
                {"detail": "You cannot mark this appointment as no-show."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {
                    "detail": (
                        "Only confirmed appointments can be marked as no-show."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.NO_SHOW
        appointment.save(update_fields=["status", "updated_at"])

        # Notification AFTER successful save
        AppointmentNotificationService.notify_no_show(appointment)

        return Response(
            AppointmentSerializer(
                appointment, context={"request": request}
            ).data
        )


# ---------------------------------------------------------------------------
# Reschedule
# ---------------------------------------------------------------------------

class AppointmentRescheduleView(APIView):
    """
    Allows the patient (or staff) to move a pending/confirmed appointment
    to a new date/time. Keeps the same doctor and duration.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(get_base_queryset(), pk=pk)

        is_patient = (
            get_user_patient(request.user)
            and appointment.patient_id == get_user_patient(request.user).id
        )
        if not (is_patient or request.user.is_staff):
            return Response(
                {"detail": "You cannot reschedule this appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status not in (
            Appointment.Status.PENDING,
            Appointment.Status.CONFIRMED,
        ):
            return Response(
                {
                    "detail": (
                        "Only pending or confirmed appointments can be rescheduled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AppointmentRescheduleSerializer(
            data=request.data,
            context={"appointment": appointment, "request": request},
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Capture old values BEFORE mutation (needed for notification)
        old_date = appointment.appointment_date
        old_time = appointment.appointment_time

        try:
            with transaction.atomic():
                appointment.appointment_date = data["appointment_date"]
                appointment.appointment_time = data["appointment_time"]
                if "reason_for_visit" in data and data["reason_for_visit"]:
                    appointment.reason_for_visit = data["reason_for_visit"]

                # Reset confirmation if it was already confirmed
                if appointment.status == Appointment.Status.CONFIRMED:
                    appointment.status = Appointment.Status.PENDING
                    appointment.confirmed_at = None

                appointment.save(
                    update_fields=[
                        "appointment_date",
                        "appointment_time",
                        "reason_for_visit",
                        "status",
                        "confirmed_at",
                        "updated_at",
                    ]
                )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "The selected appointment slot is no longer available."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Notification AFTER successful commit
        AppointmentNotificationService.notify_rescheduled(
            appointment,
            old_date=old_date,
            old_time=old_time,
        )

        # Refresh with relations
        appointment = get_base_queryset().get(pk=appointment.pk)
        return Response(
            AppointmentSerializer(
                appointment, context={"request": request}
            ).data
        )