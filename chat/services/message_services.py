from django.db import transaction

from chat.models import Message


class MessageService:

    @staticmethod
    @transaction.atomic
    def create_message(
        *,
        conversation,
        sender,
        content,
        message_type="text",
    ):
        content = (content or "").strip()

        if message_type == "text" and not content:
            raise ValueError(
                "Text message cannot be empty."
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            message_type=message_type,
        )

        conversation.save(
            update_fields=["updated_at"]
        )

        return message