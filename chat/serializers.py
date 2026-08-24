from rest_framework import serializers

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
)


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ConversationParticipant
        fields = [
            "user_id",
            "username",
            "full_name",
            "is_admin",
            "joined_at",
        ]

    def get_full_name(self, obj):
        user = obj.user

        if hasattr(user, "get_full_name"):
            return user.get_full_name()

        return user.username


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(
        source="sender.id",
        read_only=True,
    )

    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True,
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender_id",
            "sender_username",
            "content",
            "message_type",
            "created_at",
            "updated_at",
            "is_edited",
            "is_deleted",
        ]

        read_only_fields = [
            "id",
            "conversation",
            "sender_id",
            "sender_username",
            "created_at",
            "updated_at",
            "is_edited",
            "is_deleted",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "conversation_type",
            "name",
            "participants",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "participants",
            "created_at",
            "updated_at",
        ]
        