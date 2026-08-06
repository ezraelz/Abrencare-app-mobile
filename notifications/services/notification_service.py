# notifications/services/notification_service.py
from django.db import transaction
from notifications.models import Notification
from notifications.services.websocket_service import WebSocketService


class NotificationService:
    @classmethod
    @transaction.atomic
    def create(cls,*,user,title,message,notification_type,data=None,
    ):
        """
        Create a notification and immediately broadcast it.
        """

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {},
        )

        transaction.on_commit(
    lambda: WebSocketService.send_notification(
        user.id,
        notification.to_payload(),
    )
)

        return notification

    @classmethod
    @transaction.atomic
    def broadcast(
        cls,
        *,
        users,
        title,
        message,
        notification_type,
        data=None,
    ):

        notifications = []

        for user in users:

            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data or {},
            )

            notifications.append(notification)

            transaction.on_commit(
                lambda user_id=user.id,
                       payload=notification.to_payload():
                    WebSocketService.send_notification(
                        user_id,
                        payload,
                    )
            )

        return notifications