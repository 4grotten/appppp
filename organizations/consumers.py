import asyncio
import json
import logging

import websockets
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from organizations.services.assistant_services import ChatService, AssistantService
from shop.serializers.comment_serializers import CommentSerializer, WSCommentSerializer
from shop.services.comment_services import CommentService

logger = logging.getLogger(__name__)

class CommentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.chat = await self.get_chat(self.chat_id)
            self.chat_group_name = f'chat_{self.chat_id}'
            self.headers = self.scope['headers']
            self.host = self.extract_host()

            if not self.chat:
                logger.warning(f"Chat not found for ID {self.chat_id}")
                await self.close()
                return

            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)

            if self.scope['user'].is_authenticated:
                subprotocol = self.scope.get('subprotocol', None)
                await self.accept(subprotocol=subprotocol) if subprotocol else await self.accept()
            else:
                logger.warning("Unauthorized user attempted to connect.")
                await self.close()

            self.ai_socket = await self.connect_to_ai()

        except Exception as e:
            logger.error(f"Error in connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        if hasattr(self, 'ai_socket') and self.ai_socket.open:
            await self.ai_socket.close()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            assistant_id = data.get('assistant_id', None)
            user = self.scope['user']

            if assistant_id is None:
                comment = await self.handle_user_response(data, user)
                await self.send_message_to_ai(comment)
            else:
                await self.handle_ai_response(data, user)
        except Exception as e:
            logger.error(f"Error in receive: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message'], ensure_ascii=False))



    @database_sync_to_async
    def get_chat(self, chat_id):
        return ChatService.get(pk=chat_id)

    @database_sync_to_async
    def get_chat_with_parent(self, parent):
        return parent.chat

    @database_sync_to_async
    def get_assistant(self, assistant_id):
        assistant = AssistantService.get(pk=assistant_id)
        return assistant

    @database_sync_to_async
    def get_comment(self, comment_id):
        return CommentService.get(pk=comment_id)

    @database_sync_to_async
    def create_user_comment(self, text, chat, user, parent=None):
        return CommentService.create_chat_comment(text=text, chat=chat, user=user, parent=parent)

    @database_sync_to_async
    def create_comment_with_ai_response(self, text, chat, assistant, parent=None):
        return CommentService.create_chat_assistant_comment(text=text, chat=chat, assistant=assistant, parent=parent)

    @database_sync_to_async
    def serialize_data(self, comment, user):
        fake_request = type('FakeRequest', (object,), {'user': user})()
        serializer = CommentSerializer(comment, context={'request': fake_request})
        return serializer.data

    @database_sync_to_async
    def serialize_assistant_data(self, comment, user):
        serializer = WSCommentSerializer(comment, context={'user': user})
        return serializer.data


    @database_sync_to_async
    def prepare_data(self, comment):
        decoded_headers = {k.decode('utf-8'): v.decode('utf-8') for k, v in self.headers}
        data = {
            "assistant_id": comment.chat.assistant.id,
            "parent_id": comment.id,
            "chat_id": comment.chat.id,
            "message": comment.text,
            "host": self.host,
            "training_data": CommentService.get_training_data(assistant=comment.chat.assistant),
            "headers": decoded_headers
        }
        return data

    async def handle_user_response(self, data, user):
        try:
            text = data.get('message', '')
            parent_id = data.get('parent', None)
            chat = self.chat
            parent = await self.get_comment(parent_id) if parent_id else None
            comment = await self.create_user_comment(text, chat, user, parent)
            serialized_data = await self.serialize_data(comment=comment, user=user)
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': serialized_data
                }
            )
            return comment
        except Exception as e:
            logger.error(f"Error handling user response: {e}")

    async def handle_ai_response(self, data, user):
        try:
            text = data.get('message', '')
            parent_id = data.get('parent', None)
            assistant_id = data.get('assistant_id', None)
            assistant = await self.get_assistant(assistant_id)
            parent = await self.get_comment(parent_id)
            chat = await self.get_chat_with_parent(parent)
            comment = await self.create_comment_with_ai_response(text, chat, assistant, parent)
            serialized_data = await self.serialize_assistant_data(comment=comment, user=user)
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': serialized_data
                }
            )
        except Exception as e:
            logger.error(f"Error handling AI response: {e}")

    async def connect_to_ai(self):
        try:
            ai_socket = await websockets.connect('ws://161.35.153.151:8081/ws/bot/', timeout=5)
            return ai_socket
        except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to connect to AI socket: {e}")
            await self.close()

    async def send_message_to_ai(self, comment):
        try:
            data = await self.prepare_data(comment)
            await self.ai_socket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending message to AI: {e}")

    def extract_host(self):
        for header in self.scope['headers']:
            if header[0] == b'host':
                return header[1].decode('utf-8')
        return 'default_host'
