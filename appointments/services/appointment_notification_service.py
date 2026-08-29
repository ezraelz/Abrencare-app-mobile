from notifications.models import NotificationType
from notifications.services.notification_service import NotificationService


class AppointmentNotificationService:
    """
    Central place for all appointment-related notifications.
    Keep methods small and side-effect free except for the notification itself.
    """

    @staticmethod
    def _safe_create(**kwargs):
        """Never let notification failures break the main business action."""
        try:
            NotificationService.create(**kwargs)
        except Exception:
            # In production: log the exception (Sentry, structlog, etc.)
            # logger.exception("Failed to create appointment notification")
            pass

    @classmethod
    def notify_created(cls, appointment):
        doctor_name = appointment.doctor.user.get_full_name()
        patient_name = appointment.patient.user.get_full_name()
        when = f"{appointment.appointment_date} at {appointment.appointment_time}"

        # Patient
        cls._safe_create(
            user=appointment.patient.user,
            title="Appointment Scheduled",
            message=(
                f"Your appointment with Dr. {doctor_name} "
                f"has been scheduled for {when}."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "created",
            },
        )

        # Doctor
        cls._safe_create(
            user=appointment.doctor.user,
            title="New Appointment Request",
            message=(
                f"New appointment request from {patient_name} "
                f"on {when}."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "created",
            },
        )

    @classmethod
    def notify_confirmed(cls, appointment):
        doctor_name = appointment.doctor.user.get_full_name()
        when = f"{appointment.appointment_date} at {appointment.appointment_time}"

        cls._safe_create(
            user=appointment.patient.user,
            title="Appointment Confirmed",
            message=(
                f"Your appointment with Dr. {doctor_name} "
                f"on {when} has been confirmed."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "confirmed",
            },
        )

    @classmethod
    def notify_cancelled(cls, appointment, cancelled_by=None):
        doctor_name = appointment.doctor.user.get_full_name()
        patient_name = appointment.patient.user.get_full_name()
        when = f"{appointment.appointment_date} at {appointment.appointment_time}"

        actor = "the clinic"
        if cancelled_by:
            if cancelled_by == appointment.patient.user:
                actor = "you"
            elif cancelled_by == appointment.doctor.user:
                actor = f"Dr. {doctor_name}"
            else:
                actor = "the clinic"

        # Patient
        cls._safe_create(
            user=appointment.patient.user,
            title="Appointment Cancelled",
            message=(
                f"Your appointment with Dr. {doctor_name} "
                f"on {when} has been cancelled by {actor}."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "cancelled",
            },
        )

        # Doctor
        cls._safe_create(
            user=appointment.doctor.user,
            title="Appointment Cancelled",
            message=(
                f"The appointment with {patient_name} "
                f"on {when} has been cancelled."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "cancelled",
            },
        )

    @classmethod
    def notify_rescheduled(cls, appointment, old_date=None, old_time=None):
        doctor_name = appointment.doctor.user.get_full_name()
        patient_name = appointment.patient.user.get_full_name()
        new_when = f"{appointment.appointment_date} at {appointment.appointment_time}"

        old_when = None
        if old_date and old_time:
            old_when = f"{old_date} at {old_time}"

        message_patient = (
            f"Your appointment with Dr. {doctor_name} "
            f"has been rescheduled to {new_when}."
        )
        if old_when:
            message_patient = (
                f"Your appointment with Dr. {doctor_name} "
                f"has been moved from {old_when} to {new_when}."
            )

        cls._safe_create(
            user=appointment.patient.user,
            title="Appointment Rescheduled",
            message=message_patient,
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "rescheduled",
            },
        )

        cls._safe_create(
            user=appointment.doctor.user,
            title="Appointment Rescheduled",
            message=(
                f"The appointment with {patient_name} "
                f"has been rescheduled to {new_when}."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "rescheduled",
            },
        )

    @classmethod
    def notify_completed(cls, appointment):
        # Usually only the patient cares
        cls._safe_create(
            user=appointment.patient.user,
            title="Appointment Completed",
            message="Your appointment has been marked as completed.",
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "completed",
            },
        )

    @classmethod
    def notify_no_show(cls, appointment):
        # Optional – some clinics notify the patient
        cls._safe_create(
            user=appointment.patient.user,
            title="Missed Appointment",
            message=(
                "You were marked as a no-show for your recent appointment. "
                "Please contact the clinic if this is incorrect."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
                "event": "no_show",
            },
        )
        