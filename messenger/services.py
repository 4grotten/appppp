from common.exceptions import ObjectNotFoundException
from messenger.models import ChatFolder, MessengerChat, MessageLike, ChatMessage
from django.utils.translation import gettext_lazy as _
from django.db.models import Exists, OuterRef

from users.models import User


class MessengerChatService:
    model = MessengerChat

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get(cls, *args, **kwargs) -> MessengerChat:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_("MessengerChat not found"))

    @classmethod
    def is_message_liked_by_user(cls, message: ChatMessage, user: User) -> bool:
        return MessageLike.objects.filter(user=user, message=message).exists()

    @classmethod
    def sort_by(cls, queryset, sort_by: str, user=None):
        if sort_by == "new":
            return queryset.order_by("-created_at")

        elif sort_by == "unread" and user:
            unread_subquery = ChatMessage.objects.filter(
                chat=OuterRef("pk"),
                is_read=False,
            )
            return (
                queryset.annotate(has_unread=Exists(unread_subquery))
                .filter(has_unread=True)
                .order_by("-created_at")
            )

        elif sort_by == "blocked" and user:
            return queryset.filter(blockedchat__blocked_by=user).order_by("-created_at")

        return queryset.order_by("-created_at")


class ChatMessageService:
    model = ChatMessage

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get(cls, *args, **kwargs) -> ChatMessage:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_("ChatMessage not found"))

    @classmethod
    def create_chat_message(
        cls,
        text: str,
        chat: MessengerChat,
        user: User,
        parent: ChatMessage = None,
        is_read: bool = False,
    ):
        message = cls.model.objects.create(
            chat=chat, sender=user, parent=parent, text=text, is_read=is_read
        )

        return message

    @classmethod
    def like_unlike_message(
        cls, message: ChatMessage, user: User, is_liked: bool
    ) -> bool:
        if is_liked:
            MessageLike.objects.update_or_create(user=user, message=message)
        else:
            MessageLike.objects.filter(user=user, message=message).delete()

    @classmethod
    def delete_message(cls, message: ChatMessage):
        message.delete()


class FoldersChatSerivice:
    model = ChatFolder

    @classmethod
    def create(cls, user: User, data: dict):
        chat_ids = data.pop("chats", [])
        folder = cls.model.objects.create(user=user, **data)
        folder.chats.set(chat_ids)
        return folder
