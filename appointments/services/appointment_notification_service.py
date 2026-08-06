from notifications.models import NotificationType
from notifications.services.notification_service import NotificationService


class AppointmentNotificationService:

    @classmethod
    def notify_created(cls, appointment):

        NotificationService.create(
            user=appointment.patient.user,
            title="Appointment Confirmed",
            message=(
                f"Your appointment with "
                f"Dr. {appointment.doctor.user.get_full_name()} "
                f"has been scheduled for "
                f"{appointment.appointment_date}."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
            },
        )

        NotificationService.create(
            user=appointment.doctor.user,
            title="New Appointment",
            message=(
                f"You have a new appointment with "
                f"{appointment.patient.user.get_full_name()}."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
            },
        )

    @classmethod
    def notify_updated(cls, appointment):

        NotificationService.create(
            user=appointment.patient.user,
            title="Appointment Updated",
            message=(
                f"Your appointment with "
                f"Dr. {appointment.doctor.user.get_full_name()} "
                f"has been updated."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
            },
        )

        NotificationService.create(
            user=appointment.doctor.user,
            title="Appointment Updated",
            message=(
                f"The appointment with "
                f"{appointment.patient.user.get_full_name()} "
                f"has been updated."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
            },
        )

    @classmethod
    def notify_cancelled(cls, appointment):

        NotificationService.create(
            user=appointment.patient.user,
            title="Appointment Cancelled",
            message="Your appointment has been cancelled.",
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
            },
        )

        NotificationService.create(
            user=appointment.doctor.user,
            title="Appointment Cancelled",
            message=(
                f"The appointment with "
                f"{appointment.patient.user.get_full_name()} "
                f"has been cancelled."
            ),
            notification_type=NotificationType.APPOINTMENT,
            data={
                "appointment_id": appointment.id,
            },
        )
        