from common.exceptions import ObjectNotFoundException
from messenger.models import MessengerChat, MessageLike, ChatMessage
from django.utils.translation import gettext_lazy as _

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
            raise ObjectNotFoundException(_('MessengerChat not found'))

    @classmethod
    def is_message_liked_by_user(cls, message: ChatMessage, user: User) -> bool:
        return MessageLike.objects.filter(user=user, message=message).exists()

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
            raise ObjectNotFoundException(_('ChatMessage not found'))

    @classmethod
    def create_chat_message(cls, text: str, chat: MessengerChat, user: User, parent: ChatMessage = None):
        message = cls.model.objects.create(chat=chat, sender=user, parent=parent, text=text)

        return message


