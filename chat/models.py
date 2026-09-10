# chat/models.py

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    CONVERSATION_TYPES = (
        ("private", "Private"),
        ("group", "Group"),
    )

    conversation_type = models.CharField(
        max_length=20,
        choices=CONVERSATION_TYPES,
        default="private"
    )

    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_participations",
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    is_admin = models.BooleanField(
        default=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_participant",
            )
        ]

    def __str__(self):
        return f"{self.user} - Conversation {self.conversation_id}"


class Message(models.Model):
    MESSAGE_TYPES = (
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("audio", "Audio"),
        ("video", "Video"),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )

    content = models.TextField(
        blank=True
    )

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default="text",
    )

    file = models.FileField(
        upload_to="chat_attachments/%Y/%m/",
        blank=True,
        null=True,
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_edited = models.BooleanField(
        default=False
    )

    is_deleted = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"]
            ),
            models.Index(
                fields=["sender", "created_at"]
            ),
        ]

    def __str__(self):
        return (
            f"Message {self.id} "
            f"from {self.sender}"
        )
    
