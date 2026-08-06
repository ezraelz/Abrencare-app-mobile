from notifications.models import NotificationType
from notifications.services.notification_service import NotificationService
from accounts.models import User


class PatientNotificationService:

    @classmethod
    def notify_created(cls, patient):

        admins = User.objects.filter(role__role_name="admin")

        for admin in admins:
            NotificationService.create(
                user=admin,
                title="New Patient Registered",
                message=(
                    f"{patient.get_full_name() or patient.username} "
                    f"registered on {patient.date_joined:%Y-%m-%d %H:%M}."
                ),
                notification_type=NotificationType.SYSTEM,
                data={
                    "patient_id": patient.id,
                },
            )

        NotificationService.create(
            user=patient,
            title="Welcome to AbrenCare",
            message="Your account has been created successfully.",
            notification_type=NotificationType.SYSTEM,
            data={
                "patient_id": patient.id,
            },
        )
        