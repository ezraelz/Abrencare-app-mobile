# chat/services/message_services.py

from django.db import transaction

from chat.models import Message


class MessageService:

    @staticmethod
    @transaction.atomic
    def create_message(
        *,
        conversation,
        sender,
        content="",
        message_type="text",
        file=None,
    ):
        content = (content or "").strip()

        if message_type == "text" and not content:
            raise ValueError("Text message cannot be empty.")

        if message_type in ("image", "file", "audio", "video") and not file:
            raise ValueError("A file is required for this message type.")

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            message_type=message_type,
        )

        if file:
            message.file = file
            message.file_name = file.name
            message.file_size = file.size
            message.save(update_fields=["file", "file_name", "file_size"])

        conversation.save(update_fields=["updated_at"])

        return message
    