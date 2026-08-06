# notifications/consumers.py

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    RATE_LIMIT_SECONDS = 3
    MAX_MESSAGE_SIZE = 2048

    async def connect(self):
        self.user = self.scope.get("user")
        if not await self.authenticate():
            return

        if not await self.check_rate_limit():
            return

        await self.join_group()
        await self.accept()
        await self.send_connection_success()

    async def disconnect(self, close_code): 
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

        logger.info(
            "Notification websocket disconnected",
            extra={
                "user": getattr(self.user, "id", None),
                "code": close_code,
            },
        )

    async def receive(self, text_data=None, bytes_data=None):

        if not text_data:
            return

        if len(text_data) > self.MAX_MESSAGE_SIZE:
            await self.close(code=4009)
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = payload.get("type")

        if message_type == "ping":
            await self.send_json(
                {
                    "type": "pong",
                    "timestamp": timezone.now().isoformat(),
                }
            )

    async def notify(self, event):
        try:
            await self.send_json({
                "type": "notification",
                "data": event.get("payload", {}),
            })
        except Exception:
            logger.exception("Failed to send notification.")

    #############################################################
    # Private methods
    #############################################################

    async def authenticate(self):

        if not self.user or self.user.is_anonymous:
            logger.warning("Anonymous websocket rejected")
            await self.close(code=4001)
            return False
        return True

    async def check_rate_limit(self):
        key = f"notification-ws:{self.user.id}"
        if cache.get(key):
            logger.warning(
                "Rate limited websocket",
                extra={"user": self.user.id},
            )

            await self.close(code=4008)

            return False

        cache.set(key, True, timeout=self.RATE_LIMIT_SECONDS)

        return True

    async def join_group(self):
        self.group_name = f"user_notifications_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

    async def send_connection_success(self):
        await self.send_json(
            {
                "type": "connection_established",
                "user_id": self.user.id,
                "server_time": timezone.now().isoformat(),
            }
        )

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))
