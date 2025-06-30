from django.contrib import admin
from messenger.models import (
    MessengerChat,
    ChatMember,
    ChatMessage,
    MessageLike,
    BlockedChat,
    ChatFolder,
)


@admin.register(MessengerChat)
class MessengerChatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat_type",
        "title",
        "is_blocked_display",
        "created_at",
        "updated_at",
    )
    list_filter = ("chat_type",)
    search_fields = ("title",)
    filter_horizontal = ("members",)

    def is_blocked_display(self, obj):
        return obj.is_blocked()

    is_blocked_display.short_description = "Blocked"
    is_blocked_display.boolean = True


@admin.register(ChatMember)
class ChatMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "user", "joined_at", "last_read_at")
    list_filter = ("joined_at", "last_read_at")
    search_fields = ("user__phone", "chat__title")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat",
        "sender",
        "short_text",
        "is_sent",
        "is_delivered",
        "is_read",
        "created_at",
    )
    list_filter = ("is_sent", "is_delivered", "is_read", "created_at")
    search_fields = ("text", "sender__phone", "chat__title")

    def short_text(self, obj):
        return obj.text[:40] + ("..." if len(obj.text) > 40 else "")

    short_text.short_description = "Text"


@admin.register(MessageLike)
class MessageLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "user")
    search_fields = ("user__phone", "message__text")


@admin.register(BlockedChat)
class BlockedChatAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "blocked_by", "blocked_at")
    search_fields = ("chat__title", "blocked_by__phone")
    readonly_fields = ("blocked_at",)


@admin.register(ChatFolder)
class ChatFolderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title")
    search_fields = ("user__phone", "title")
    filter_horizontal = ("chats",)
