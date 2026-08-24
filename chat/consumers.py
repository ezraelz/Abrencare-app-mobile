import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import (
    ConversationParticipant,
    Message,
)


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = (
            self.scope["url_route"]["kwargs"][
                "conversation_id"
            ]
        )

        self.room_group_name = (
            f"chat_{self.conversation_id}"
        )

        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        is_participant = (
            await self.check_participant(
                user.id,
                self.conversation_id,
            )
        )

        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection",
                    "message": "Connected to chat.",
                    "conversation_id": (
                        int(self.conversation_id)
                    ),
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error(
                "Invalid JSON."
            )
            return

        message_type = data.get("type")

        if message_type == "message":
            await self.handle_message(data)
            return

        if message_type == "typing":
            await self.handle_typing(data)
            return

        await self.send_error(
            "Unknown message type."
        )

    async def handle_message(self, data):
        content = data.get(
            "content",
            "",
        )

        content = content.strip()

        if not content:
            await self.send_error(
                "Message cannot be empty."
            )
            return

        user = self.scope["user"]

        message = await self.create_message(
            user.id,
            self.conversation_id,
            content,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message["id"],
                    "conversation": message[
                        "conversation"
                    ],
                    "sender_id": message[
                        "sender_id"
                    ],
                    "sender_username": message[
                        "sender_username"
                    ],
                    "content": message[
                        "content"
                    ],
                    "message_type": message[
                        "message_type"
                    ],
                    "created_at": message[
                        "created_at"
                    ],
                },
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": event["message"],
                }
            )
        )

    async def send_error(self, message):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )

    @database_sync_to_async
    def check_participant(
        self,
        user_id,
        conversation_id,
    ):
        return (
            ConversationParticipant.objects
            .filter(
                user_id=user_id,
                conversation_id=conversation_id,
            )
            .exists()
        )

    @database_sync_to_async
    def create_message(
        self,
        user_id,
        conversation_id,
        content,
    ):
        from django.contrib.auth import get_user_model

        from .models import Conversation
        from .services.message_services import (
            MessageService,
        )

        User = get_user_model()

        conversation = Conversation.objects.get(
            id=conversation_id
        )

        user = User.objects.get(
            id=user_id
        )

        message = MessageService.create_message(
            conversation=conversation,
            sender=user,
            content=content,
            message_type="text",
        )

        return {
            "id": message.id,
            "conversation": message.conversation_id,
            "sender_id": message.sender_id,
            "sender_username": message.sender.username,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
        }

    async def handle_typing(self, data):
        is_typing = data.get(
            "is_typing",
            False,
        )

        user = self.scope["user"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_status",
                "user_id": user.id,
                "username": user.username,
                "is_typing": bool(is_typing),
            },
        )

    async def typing_status(self, event):
        user = self.scope["user"]

        # Don't send the typing event back
        # to the person who generated it.
        if event["user_id"] == user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "is_typing": event["is_typing"],
                }
            )
        )