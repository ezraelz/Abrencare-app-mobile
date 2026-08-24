from django.contrib import admin

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation_type",
        "name",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "conversation_type",
    )

    search_fields = (
        "name",
    )


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "user",
        "is_admin",
        "joined_at",
    )

    list_filter = (
        "is_admin",
    )

    search_fields = (
        "user__username",
        "user__email",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "message_type",
        "created_at",
        "is_edited",
        "is_deleted",
    )

    list_filter = (
        "message_type",
        "is_edited",
        "is_deleted",
    )

    search_fields = (
        "content",
        "sender__username",
    )