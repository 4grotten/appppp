from decouple import config
import logging
import json
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
import aioredis

from messenger.serializers import ChatMessageCreateSerializer, ChatMessageWSSerializer
from messenger.services import ChatMessageService, MessengerChatService

User = get_user_model()

REDIS_URL = f"redis://{config('REDIS_HOST', 'redis')}:{config('REDIS_PORT', default=6379, cast=int)}"

logger = logging.getLogger(__name__)
redis = None


async def get_redis():
    global redis
    if not redis:
        redis = await aioredis.create_redis_pool(REDIS_URL)
    return redis


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
            self.room_group_name = f"chat_{self.chat_id}"
            self.headers = self.scope["headers"]
            self.host = self.extract_host()

            subprotocol = None
            for header in self.scope["headers"]:
                if header[0].decode().lower() == "sec-websocket-protocol":
                    subprotocol = header[1].decode()
                    break

            if not self.scope["user"].is_authenticated:
                logger.warning("Unauthorized user attempted to connect.")
                await self.close()
                return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            user_id = str(self.scope["user"].id)
            redis_conn = await get_redis()
            chat_key = f"chat_{self.chat_id}_online_users"
            await redis_conn.sadd(chat_key, user_id)

            if subprotocol:
                await self.accept(subprotocol=subprotocol)
            else:
                await self.accept()
        except Exception as e:
            logger.error(f"Error in connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        user_id = str(self.scope["user"].id)
        chat_key = f"chat_{self.chat_id}_online_users"
        redis_conn = await get_redis()
        await redis_conn.srem(chat_key, user_id)

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope.get("user")

        serializer = ChatMessageCreateSerializer(data=data, context={"user": user})
        is_valid = await sync_to_async(serializer.is_valid)()
        if not is_valid:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "Invalid input",
                        "errors": serializer.errors,
                    }
                )
            )
            return

        self.chat = await self.get_chat(self.chat_id)

        # Проверяем есть ли другие онлайн пользователи в этом чате кроме отправителя
        user_id = str(user.id)
        redis_conn = await get_redis()
        chat_key = f"chat_{self.chat_id}_online_users"
        online_users = await redis_conn.smembers(chat_key)
        online_user_ids = set([u.decode("utf-8") for u in online_users])
        interlocutor_online = any(uid != user_id for uid in online_user_ids)

        # Создаем сообщение с is_read = True, если собеседник онлайн, иначе False
        message = await self.send_message(
            chat=self.chat,
            user=user,
            text=serializer.validated_data["text"],
            parent=serializer.validated_data.get("parent"),
            is_read=interlocutor_online,
        )

        serializer = ChatMessageWSSerializer(message, context={"user": user})
        response_json = await sync_to_async(lambda: serializer.data.copy())()

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": response_json}
        )
        participant_ids = [str(uid) for uid in online_user_ids]
        for user_id in participant_ids:
            await self.channel_layer.group_send(
                f"user_{user_id}_chats",
                {
                    "type": "chat_list_update",
                    "chat_id": self.chat_id,
                    "last_message": response_json,
                },
            )

    async def chat_message(self, event):
        message_data = event["message"]

        message_id = message_data.get("id")
        await self.mark_as_read(message_id, self.scope["user"])

        await self.send(text_data=json.dumps(message_data))

    @database_sync_to_async
    def mark_as_read(self, message_id, user):
        from messenger.models import ChatMessage

        try:
            message = ChatMessage.objects.get(id=message_id)
            if message.sender != user:
                message.is_delivered = True
                message.is_read = True
                message.save(update_fields=["is_delivered", "is_read"])
        except ChatMessage.DoesNotExist:
            pass

    @database_sync_to_async
    def get_chat(self, chat_id):
        return MessengerChatService.get(pk=chat_id)

    @database_sync_to_async
    def send_message(self, chat, user, text, parent=None, is_read=False):
        return ChatMessageService.create_chat_message(
            chat=chat,
            user=user,
            text=text,
            parent=parent,
            is_read=is_read,
        )

    def extract_host(self):
        for header in self.scope["headers"]:
            if header[0] == b"host":
                return header[1].decode("utf-8")
        return "default_host"


class ChatListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        subprotocol = None
        for header in self.scope["headers"]:
            if header[0].decode().lower() == "sec-websocket-protocol":
                subprotocol = header[1].decode()
                break
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.user = self.scope["user"]
        self.room_group_name = f"user_{self.user.id}_chats"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        if subprotocol:
            await self.accept(subprotocol=subprotocol)
        else:
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def chat_list_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event": "chat_updated",
                    "chat_id": event["chat_id"],
                    "last_message": event["last_message"],
                }
            )
        )
