# notifications/selectors/notification_selector.py

from notifications.models import Notification


class NotificationSelector:

    @classmethod
    def for_user(cls, user):

        return (
            Notification.objects.filter(user=user)
            .only(
                "id",
                "title",
                "message",
                "notification_type",
                "created_at",
                "is_read",
                "data",
            )
            .order_by("-created_at")
        )

    @classmethod
    def unread(cls, user):

        return (
            Notification.objects.filter(
                user=user,
                is_read=False,
            )
            .only(
                "id",
                "title",
                "message",
                "notification_type",
                "created_at",
            )
            .order_by("-created_at")
        )

    @classmethod
    def get_user_notification(cls, user, pk):

        return Notification.objects.get(
            user=user,
            pk=pk,
        )