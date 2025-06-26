import logging

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from messenger.serializers import ChatMessageCreateSerializer, ChatMessageSerializer, ChatMessageWSSerializer
from messenger.models import MessengerChat
from messenger.services import ChatMessageService, MessengerChatService

User = get_user_model()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.room_group_name = f'chat_{self.chat_id}'
            self.headers = self.scope['headers']
            self.host = self.extract_host()

            subprotocol = None
            for header in self.scope['headers']:
                if header[0].decode().lower() == 'sec-websocket-protocol':
                    subprotocol = header[1].decode()
                    break

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            if not self.scope['user'].is_authenticated:
                logger.warning("Unauthorized user attempted to connect.")
                await self.close()
                return

            if subprotocol:
                await self.accept(subprotocol=subprotocol)
            else:
                await self.accept()
        except Exception as e:
            logger.error(f"Error in connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope.get("user")

        serializer = ChatMessageCreateSerializer(data=data, context={'user': user})
        if not serializer.is_valid():
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid input',
                'errors': serializer.errors
            }))
            return

        self.chat = await self.get_chat(self.chat_id)

        message = await self.send_message(
            chat=self.chat,
            user=user,
            text=serializer.validated_data["text"],
            parent=serializer.validated_data.get("parent")
        )

        response_data = await sync_to_async(ChatMessageWSSerializer)(message, context={'user': user})
        response_json = await sync_to_async(lambda s: s.data)(response_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': response_json
            }
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
    def send_message(self, chat, user, text, parent=None):
        return ChatMessageService.create_chat_message(
            chat=chat,
            user=user,
            text=text,
            parent=parent
        )

    def extract_host(self):
        for header in self.scope['headers']:
            if header[0] == b'host':
                return header[1].decode('utf-8')
        return 'default_host'