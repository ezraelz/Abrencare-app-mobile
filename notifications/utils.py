# notifications/utils.py
from django.utils import timezone


def websocket_payload(notification):

    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "created_at": timezone.localtime(
            notification.created_at
        ).isoformat(),
        "is_read": notification.is_read,
        "data": notification.data,
    }
