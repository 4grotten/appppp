from django.db import models
from django.utils import timezone

from common.models import TimestampModel
from messenger.constants import CHAT_TYPES, MEMBER, ROLE_CHOICES
from users.models import User


class MessengerChat(TimestampModel):
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPES)
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="chat_images", null=True, blank=True)
    members = models.ManyToManyField(
        User, through="ChatMember", related_name="messenger_chats"
    )

    def __str__(self):
        return self.title or f"{self.chat_type} chat #{self.id}"

    def is_blocked(self):
        return hasattr(self, "blockedchat")

    def is_blocked_by(self, user):
        return self.is_blocked() and self.blockedchat.blocked_by == user


class ChatMember(TimestampModel):
    chat = models.ForeignKey(MessengerChat, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_memberships"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("chat", "user")


class ChatMessage(TimestampModel):
    chat = models.ForeignKey(
        MessengerChat, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messenger_sent_messages"
    )
    text = models.TextField()
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies"
    )
    is_sent = models.BooleanField(default=True)
    is_delivered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    forwarded_from = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forwarded_messages",
        help_text="Оригинальный отправитель пересланного сообщения",
    )
    forwarded_message = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forwards",
        help_text="Исходное сообщение, которое переслали",
    )

    class Meta:
        ordering = ["created_at"]

    @property
    def is_forwarded(self):
        return self.forwarded_from is not None or self.forwarded_message is not None


class MessageLike(models.Model):
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="likes"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("message", "user")


class BlockedChat(models.Model):
    chat = models.OneToOneField(MessengerChat, on_delete=models.CASCADE)
    blocked_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blocked_chats"
    )
    blocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["chat"], name="one_block_per_chat")
        ]


class ChatFolder(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_folders"
    )
    title = models.CharField(max_length=255)
    chats = models.ManyToManyField(MessengerChat, related_name="folders")

    class Meta:
        unique_together = ("user", "title")
