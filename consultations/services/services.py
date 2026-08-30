from datetime import datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from appointments.models import Appointment
from doctors.models import Doctor
from .consultation_notification_service import ConsultationNotificationService

from ..models import Consultation, Prescription

ACTIVE_APPOINTMENT_STATUSES = [
    Appointment.Status.PENDING,
    Appointment.Status.CONFIRMED,
]


def _has_conflict(doctor, appointment_date, appointment_time, duration_minutes):
    """
    Catches overlapping bookings that don't share the exact same start time
    (e.g. an existing 10:00-10:30 appointment vs. a new 10:15 request).
    The DB UniqueConstraint on Appointment only catches identical start times,
    so this check is still needed even with that constraint in place.
    """
    slot_start = datetime.combine(appointment_date, appointment_time)
    slot_end = slot_start + timedelta(minutes=duration_minutes)

    conflicting = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=ACTIVE_APPOINTMENT_STATUSES,
    )

    for appointment in conflicting:
        existing_start = datetime.combine(appointment_date, appointment.appointment_time)
        existing_end = existing_start + timedelta(minutes=appointment.duration_minutes)
        if slot_start < existing_end and slot_end > existing_start:
            return True

    return False


@transaction.atomic
def book_consultation(
    *, user, doctor, appointment_date, appointment_time,
    consultation_type, language, reason_for_visit,
):
    try:
        patient = user.patient
    except AttributeError:
        raise ValueError("Authenticated user is not linked to a patient.")

    # Lock the doctor row so concurrent booking attempts against this doctor
    # are serialized. This closes the race window for the overlap check above;
    # the DB UniqueConstraint below is a second line of defense for the
    # exact-same-slot case even if this lock were ever bypassed.
    doctor = Doctor.objects.select_for_update().get(pk=doctor.pk)
    duration_minutes = doctor.consultation_duration

    if _has_conflict(doctor, appointment_date, appointment_time, duration_minutes):
        raise ValueError("This slot is no longer available. Please choose another time.")

    appointment = Appointment(
        patient=patient,
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        duration_minutes=duration_minutes,
        status=Appointment.Status.CONFIRMED,
        confirmed_at=timezone.now(),
        reason_for_visit=reason_for_visit,
    )

    # Appointment.clean() already validates the date isn't in the past and
    # that the slot fits inside the doctor's availability windows — reuse it
    # instead of duplicating that logic here.
    try:
        appointment.full_clean()
    except DjangoValidationError as exc:
        raise ValueError(exc.message_dict) from exc

    try:
        appointment.save()
    except IntegrityError:
        # Backstop for the rare race the row lock didn't catch (e.g. a slot
        # freed up and got rebooked between the lock and this save).
        raise ValueError("This slot was just booked by someone else. Please choose another time.")

    consultation = Consultation.objects.create(
        appointment=appointment,
        consultation_type=consultation_type,
        language=language,
        status=Consultation.Status.SCHEDULED,
        price=doctor.consultation_fee,  # snapshot fee at booking time
    )

    ConsultationNotificationService.consultation_booked(consultation)

    return consultation


def cancel_consultation(*, consultation, user, reason):
    if consultation.status in (
        Consultation.Status.IN_PROGRESS,
        Consultation.Status.COMPLETED,
        Consultation.Status.CANCELLED,
        Consultation.Status.NO_SHOW,
    ):
        raise ValueError(f"Cannot cancel a consultation with status '{consultation.status}'.")

    with transaction.atomic():
        consultation.status = Consultation.Status.CANCELLED
        consultation.save(update_fields=["status", "updated_at"])

        appointment = consultation.appointment
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancelled_by = user
        appointment.cancellation_reason = reason
        appointment.save(
            update_fields=[
                "status", "cancelled_at", "cancelled_by",
                "cancellation_reason", "updated_at",
            ]
        )

        ConsultationNotificationService.consultation_cancelled(
            consultation, cancelled_by=user, reason=reason,
        )

    return consultation


def start_consultation(*, consultation, user):
    if consultation.status not in (Consultation.Status.SCHEDULED, Consultation.Status.WAITING):
        raise ValueError(f"Cannot start a consultation with status '{consultation.status}'.")

    if consultation.appointment.status != Appointment.Status.CONFIRMED:
        raise ValueError("The underlying appointment is not confirmed.")

    consultation.status = Consultation.Status.IN_PROGRESS
    consultation.started_at = timezone.now()

    if not consultation.meeting_url:
        # Placeholder — replace with your video provider's room-creation call.
        import uuid
        consultation.meeting_url = f"https://meet.example.com/{uuid.uuid4()}"

    consultation.save(update_fields=["status", "started_at", "meeting_url", "updated_at"])

    ConsultationNotificationService.consultation_started(consultation)

    return consultation


def complete_consultation(*, consultation, user):
    if consultation.status != Consultation.Status.IN_PROGRESS:
        raise ValueError(f"Cannot complete a consultation with status '{consultation.status}'.")

    with transaction.atomic():
        consultation.status = Consultation.Status.COMPLETED
        consultation.ended_at = timezone.now()
        consultation.save(update_fields=["status", "ended_at", "updated_at"])

        appointment = consultation.appointment
        appointment.status = Appointment.Status.COMPLETED
        appointment.completed_at = timezone.now()
        appointment.save(update_fields=["status", "completed_at", "updated_at"])

        ConsultationNotificationService.consultation_completed(consultation)
    return consultation


def create_prescription(*, consultation, doctor, data):
    if consultation.appointment.doctor_id != doctor.id:
        raise ValueError("You are not authorized to prescribe for this consultation.")

    if consultation.status not in (Consultation.Status.IN_PROGRESS, Consultation.Status.COMPLETED):
        raise ValueError("Prescriptions can only be created during or after the consultation.")

    prescription = Prescription.objects.create(consultation=consultation, **data)

    ConsultationNotificationService.prescription_added(consultation, prescription)

    return prescription
