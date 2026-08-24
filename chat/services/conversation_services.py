from django.db import transaction

from chat.models import (
    Conversation,
    ConversationParticipant,
)


class ConversationService:

    @staticmethod
    @transaction.atomic
    def create_private_conversation(
        user,
        other_user,
    ):
        if user.id == other_user.id:
            raise ValueError(
                "You cannot create a private conversation with yourself."
            )

        existing_conversation = (
            Conversation.objects
            .filter(
                conversation_type="private",
                participants__user=user,
            )
            .filter(
                participants__user=other_user,
            )
            .distinct()
            .first()
        )

        if existing_conversation:
            return existing_conversation

        conversation = Conversation.objects.create(
            conversation_type="private",
        )

        ConversationParticipant.objects.bulk_create(
            [
                ConversationParticipant(
                    conversation=conversation,
                    user=user,
                    is_admin=False,
                ),
                ConversationParticipant(
                    conversation=conversation,
                    user=other_user,
                    is_admin=False,
                ),
            ]
        )

        return conversation

    @staticmethod
    @transaction.atomic
    def create_group_conversation(
        user,
        name,
        participant_ids,
    ):
        conversation = Conversation.objects.create(
            conversation_type="group",
            name=name,
        )

        ConversationParticipant.objects.create(
            conversation=conversation,
            user=user,
            is_admin=True,
        )

        ConversationParticipant.objects.bulk_create(
            [
                ConversationParticipant(
                    conversation=conversation,
                    user_id=user_id,
                    is_admin=False,
                )
                for user_id in participant_ids
                if user_id != user.id
            ]
        )

        return conversation
    