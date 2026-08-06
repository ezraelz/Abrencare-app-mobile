from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Appointment, Scheduling
from .serializers import (
    AppointmentSerializer,
    SchedulingSerializer,
)

from .services.appointment_notification_service import (
    AppointmentNotificationService,
)


class AppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        AppointmentNotificationService.notify_created(appointment)

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = AppointmentSerializer(appointment)

        return Response(serializer.data)

    def put(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = AppointmentSerializer(
            appointment,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        AppointmentNotificationService.notify_updated(appointment)

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        AppointmentNotificationService.notify_cancelled(appointment)
        appointment.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SchedulingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        schedules = Scheduling.objects.all()

        serializer = SchedulingSerializer(
            schedules,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = SchedulingSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        schedule = serializer.save()

        return Response(
            SchedulingSerializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )


class SchedulingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        schedule = get_object_or_404(
            Scheduling,
            pk=pk,
        )

        serializer = SchedulingSerializer(schedule)

        return Response(serializer.data)

    def put(self, request, pk):
        schedule = get_object_or_404(
            Scheduling,
            pk=pk,
        )

        serializer = SchedulingSerializer(
            schedule,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        schedule = serializer.save()

        return Response(
            SchedulingSerializer(schedule).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        schedule = get_object_or_404(
            Scheduling,
            pk=pk,
        )

        schedule.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    