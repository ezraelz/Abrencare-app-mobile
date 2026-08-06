from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    class Meta:

        model = Notification

        fields = (
            "id",
            "title",
            "message",
            "user_name",
            "notification_type",
            "data",
            "is_read",
            "created_at",
            "read_at",
        )

        read_only_fields = fields