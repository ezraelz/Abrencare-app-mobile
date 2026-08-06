from notifications.models import NotificationType
from notifications.services.notification_service import NotificationService
from accounts.models import User


class DoctorNotificationService:

    @classmethod
    def notify_created(cls, doctor):

        admins = User.objects.filter(role__role_name="admin")

        for admin in admins:
            NotificationService.create(
                user=admin,
                title="New Doctor Registered",
                message=(
                    f"{doctor.get_full_name() or doctor.username} "
                    f"registered on {doctor.date_joined:%Y-%m-%d %H:%M}."
                ),
                notification_type=NotificationType.SYSTEM,
                data={
                    "doctor_id": doctor.id,
                },
            )

        NotificationService.create(
            user=doctor,
            title="Welcome to AbrenCare",
            message="Your account has been created successfully.",
            notification_type=NotificationType.SYSTEM,
            data={
                "doctor_id": doctor.id,
            },
        )
        