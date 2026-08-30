# consultations/services/consultation_notification_service.py
"""
Owns every notification the Consultation module sends. `services.py` (the state-machine
layer) calls one method here per event instead of building titles/messages/payloads
inline — that keeps copy and payload shape in one place, and keeps the state-machine
functions focused on what changed rather than how it's announced.

Each method is a thin wrapper around notifications.services.notification_service
.NotificationService.create, which is itself @transaction.atomic and defers the actual
websocket push to transaction.on_commit — so calling these from inside an outer
@transaction.atomic block in services.py is safe: nothing is broadcast if the outer
transaction rolls back.
"""

from notifications.services.notification_service import NotificationService


class ConsultationNotificationType:
    """
    Wire values for Notification.notification_type. Centralized here so the frontend
    guide and any future notification-preferences UI can reference the same constants
    this service uses, instead of duplicating string literals.
    """

    CONSULTATION_BOOKED = "consultation_booked"
    CONSULTATION_CANCELLED = "consultation_cancelled"
    CONSULTATION_STARTED = "consultation_started"
    CONSULTATION_COMPLETED = "consultation_completed"
    PRESCRIPTION_ADDED = "prescription_added"

    # Reserved for when the `waiting` status and a join endpoint exist.
    CONSULTATION_WAITING = "consultation_waiting"
    # Reserved for when a no-show sweep exists.
    CONSULTATION_NO_SHOW = "consultation_no_show"


class ConsultationNotificationService:
    """
    One classmethod per consultation lifecycle event. Call these from
    consultations/services.py at the point of each state transition.
    """

    @classmethod
    def consultation_booked(cls, consultation):
        """Notify the doctor that a patient booked a consultation."""
        appointment = consultation.appointment
        doctor_user = appointment.doctor.user
        patient_name = appointment.patient.user.full_name

        return NotificationService.create(
            user=doctor_user,
            title="New consultation booked",
            message=(
                f"{patient_name} booked a {consultation.consultation_type} consultation "
                f"on {appointment.appointment_date} at {appointment.appointment_time}."
            ),
            notification_type=ConsultationNotificationType.CONSULTATION_BOOKED,
            data={
                "consultation_id": consultation.id,
                "appointment_date": str(appointment.appointment_date),
                "appointment_time": str(appointment.appointment_time),
                "consultation_type": consultation.consultation_type,
            },
        )

    @classmethod
    def consultation_cancelled(cls, consultation, *, cancelled_by, reason=""):
        """
        Notify the other party that a consultation was cancelled. `cancelled_by` is the
        User who cancelled it — the notification goes to whichever side did NOT cancel,
        so a doctor-initiated cancel (once that flow exists) notifies the patient instead
        of always notifying the doctor.
        """
        appointment = consultation.appointment
        patient_user = appointment.patient.user
        doctor_user = appointment.doctor.user

        recipient = doctor_user if cancelled_by == patient_user else patient_user
        canceller_label = "The patient" if recipient == doctor_user else "The doctor"

        return NotificationService.create(
            user=recipient,
            title="Consultation cancelled",
            message=(
                f"{canceller_label} cancelled the consultation on "
                f"{appointment.appointment_date} at {appointment.appointment_time}."
                + (f" Reason: {reason}" if reason else "")
            ),
            notification_type=ConsultationNotificationType.CONSULTATION_CANCELLED,
            data={
                "consultation_id": consultation.id,
                "reason": reason,
                "cancelled_by_user_id": cancelled_by.id,
            },
        )

    @classmethod
    def consultation_started(cls, consultation):
        """Notify the patient that the doctor has started the session and a room is ready."""
        appointment = consultation.appointment
        patient_user = appointment.patient.user
        doctor_name = appointment.doctor.user.full_name

        return NotificationService.create(
            user=patient_user,
            title="Your consultation has started",
            message=f"Dr. {doctor_name} is ready for your {consultation.consultation_type} consultation.",
            notification_type=ConsultationNotificationType.CONSULTATION_STARTED,
            data={
                "consultation_id": consultation.id,
                "meeting_url": consultation.meeting_url,
                "consultation_type": consultation.consultation_type,
            },
        )

    @classmethod
    def consultation_completed(cls, consultation):
        """Notify the patient that the session has ended."""
        appointment = consultation.appointment
        patient_user = appointment.patient.user

        return NotificationService.create(
            user=patient_user,
            title="Consultation completed",
            message="Your consultation has ended. Check your prescriptions if any were issued.",
            notification_type=ConsultationNotificationType.CONSULTATION_COMPLETED,
            data={"consultation_id": consultation.id},
        )

    @classmethod
    def prescription_added(cls, consultation, prescription):
        """Notify the patient that a prescription was added to their consultation."""
        appointment = consultation.appointment
        patient_user = appointment.patient.user

        return NotificationService.create(
            user=patient_user,
            title="New prescription added",
            message=f"{prescription.medication} was added to your consultation record.",
            notification_type=ConsultationNotificationType.PRESCRIPTION_ADDED,
            data={
                "consultation_id": consultation.id,
                "prescription_id": prescription.id,
                "medication": prescription.medication,
            },
        )
    