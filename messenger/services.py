from common.exceptions import ObjectNotFoundException
from messenger.models import (
    BlockedChat,
    ChatFolder,
    MessengerChat,
    MessageLike,
    ChatMessage,
)
from django.utils.translation import gettext_lazy as _
from django.db.models import Exists, OuterRef, Subquery, DateTimeField, Value
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone
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
            last_message_subquery = (
                ChatMessage.objects.filter(chat=OuterRef("pk"))
                .order_by("-created_at")
                .values("created_at")[:1]
            )

            # Последний лайк
            last_like_subquery = (
                MessageLike.objects.filter(message__chat=OuterRef("pk"))
                .order_by("-id")
                .values("message__created_at")[:1]
            )

            queryset = queryset.annotate(
                last_message_time=Subquery(
                    last_message_subquery, output_field=DateTimeField()
                ),
                last_like_time=Subquery(
                    last_like_subquery, output_field=DateTimeField()
                ),
                latest_activity=Greatest(
                    Coalesce(
                        Subquery(last_message_subquery, output_field=DateTimeField()),
                        Value(timezone.datetime.min),
                    ),
                    Coalesce(
                        Subquery(last_like_subquery, output_field=DateTimeField()),
                        Value(timezone.datetime.min),
                    ),
                ),
            ).order_by("-latest_activity", "-created_at")

        elif sort_by == "unread" and user:
            unread_subquery = ChatMessage.objects.filter(
                chat=OuterRef("pk"),
                is_read=False,
            )
            queryset = queryset.annotate(has_unread=Exists(unread_subquery)).order_by(
                "-has_unread", "-created_at"
            )

        elif sort_by == "blocked" and user:
            queryset = queryset.annotate(
                is_blockeds=Exists(
                    BlockedChat.objects.filter(chat=OuterRef("pk"), blocked_by=user)
                )
            ).order_by("-is_blockeds", "-created_at")

        else:
            queryset = queryset.order_by("-created_at")

        return queryset


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
