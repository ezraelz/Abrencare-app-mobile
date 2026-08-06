# notifications/services/websocket_service.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class WebSocketService:
    """
    Handles all websocket communication.
    """

    @classmethod
    def send_notification(cls, user_id: int, payload: dict):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{user_id}",
            {
                "type": "notify",
                "payload": payload,
            },
        )

    @classmethod
    def send_many(cls, user_ids, payload):

        channel_layer = get_channel_layer()

        for user_id in user_ids:
            async_to_sync(channel_layer.group_send)(
                f"user_notifications_{user_id}",
                {
                    "type": "notify",
                    "payload": payload,
                },
            )