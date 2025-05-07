import asyncio
import json
import logging
import decimal

import websockets
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from organizations.models import UserAssistant
from organizations.services.assistant_services import ChatService, AssistantService, UserAssistantService
from organizations.services.organization_services import OrganizationService
from shop.serializers.comment_serializers import CommentSerializer, WSCommentSerializer
from shop.serializers.item_serializers import ItemInfoSerializer
from shop.services.comment_services import CommentService
from shop.services.item_services import ShopItemService

logger = logging.getLogger(__name__)

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    else:
        return obj

class CommentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.chat_group_name = f'chat_{self.chat_id}'
            self.headers = self.scope['headers']
            self.host = self.extract_host()

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
            self.chat = await self.get_chat(self.chat_id)
            if not self.chat:
                logger.warning(f"Chat not found for ID {self.chat_id}")
                await self.close()
                return
            logger.info("Received text data: %s", text_data)
            data = json.loads(text_data)
            logger.info("Parsed JSON data: %s", data)

            assistant_id = data.get('assistant_id', None)
            logger.info("Extracted assistant_id: %s", assistant_id)

            user = self.scope['user']
            logger.info("Retrieved user from scope: %s", user)

            chat = self.chat
            logger.info("Current chat: %s", chat)
            assistant = await self.get_assistant_by_chat(chat=chat)
            user_has_active_assistant = await self.user_has_active_assistant(assistant=assistant)
            logger.info("User has active assistant: %s", user_has_active_assistant)

            is_enabled = await self.get_chat_assistant_is_enabled_flag(chat=chat)
            logger.info("Chat assistant is enabled: %s", is_enabled)

            chat_by_org_user = await self.get_chat_chat_org_by_user(chat=chat)
            logger.info("Chat is by org user: %s", chat_by_org_user)

            if is_enabled:
                logger.info("Chat assistant is enabled.")
                if chat_by_org_user:
                    logger.info("Chat is by organization user.")
                    await self.handle_user_response(data, user)
                else:
                    logger.info("Chat is not by organization user.")
                    if user_has_active_assistant:
                        logger.info("User has an active assistant.")
                        if assistant_id is None:
                            logger.info("Assistant ID is None.")
                            comment = await self.handle_user_response(data, user)
                            logger.info("Handled user response, comment: %s", comment)
                            await self.send_message_to_ai(comment)
                            logger.info("Sent message to AI.")
                        else:
                            logger.info("Assistant ID is provided.")
                            await self.handle_ai_response(data, user)
                            logger.info("Handled AI response.")
                    else:
                        logger.info("User does not have an active assistant.")
                        await self.handle_user_response(data, user)
                        logger.info("Handled user response.")
            else:
                logger.info("Chat assistant is not enabled.")
                comment = await self.handle_user_response(data, user)
                logger.info("Handled user response, comment: %s", comment)
                await self.handle_ai_default_response(parent=comment, user=user)
                logger.info("Handled AI default response.")
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
    def get_chat_assistant_is_enabled_flag(self, chat):
        return chat.assistant.is_enabled

    @database_sync_to_async
    def get_chat_chat_org_by_user(self, chat):
        return chat.chat_by_org_user

    @database_sync_to_async
    def get_assistant_by_chat(self, chat):
        return chat.assistant

    @database_sync_to_async
    def user_has_active_assistant(cls, assistant):
        return UserAssistant.objects.filter(assistant=assistant, is_active=True).exists()

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
    def create_ai_defualt_comment(self, chat, parent=None):
        return CommentService.create_ws_chat_comment_with_assistant_default_response(chat=chat, parent=parent)

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

    async def handle_ai_default_response(self, parent, user):
        try:
            chat = await self.get_chat_with_parent(parent)
            comment = await self.create_ai_defualt_comment(chat, parent)
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
            if not hasattr(self, 'ai_socket') or self.ai_socket is None or not self.ai_socket.open:
                logger.warning("AI socket not connected. Attempting to reconnect...")
                self.ai_socket = await self.connect_to_ai()
                if not self.ai_socket or not self.ai_socket.open:
                    logger.error("Failed to reconnect to AI socket")
                    return

            data = await self.prepare_data(comment)
            logger.debug(f"Sending message to AI: {data}")
            await self.ai_socket.send(json.dumps(data))
            logger.info("Message sent to AI successfully")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection to AI closed unexpectedly: {e}")
            await self.reconnect_ai_socket()
        except Exception as e:
            logger.error(f"Error sending message to AI: {e}")
            await self.reconnect_ai_socket()

    async def reconnect_ai_socket(self):
        try:
            logger.info("Attempting to reconnect to AI socket...")
            if hasattr(self, 'ai_socket') and self.ai_socket.open:
                await self.ai_socket.close()
            self.ai_socket = await self.connect_to_ai()
        except Exception as e:
            logger.error(f"Failed to reconnect to AI socket: {e}")

    def extract_host(self):
        for header in self.scope['headers']:
            if header[0] == b'host':
                return header[1].decode('utf-8')
        return 'default_host'



class CommentItemConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.chat_group_name = f'chat_{self.chat_id}'
            self.headers = self.scope['headers']
            self.host = self.extract_item_host()

            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)

            if self.scope['user'].is_authenticated:
                subprotocol = self.scope.get('subprotocol', None)
                await self.accept(subprotocol=subprotocol) if subprotocol else await self.accept()
            else:
                logger.warning("Unauthorized user attempted to connect.")
                await self.close()

            self.ai_socket = await self.connect_to_item_ai()

        except Exception as e:
            logger.error(f"Error in connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        if hasattr(self, 'ai_socket') and self.ai_socket.open:
            await self.ai_socket.close()

    async def receive(self, text_data):
        try:
            logger.debug("Received text data: %s", text_data)
            self.chat = await self.get_chat_item(self.chat_id)
            if not self.chat:
                logger.warning(f"Chat not found for ID {self.chat_id}")
                await self.close()
                return
            logger.info("Received text data: %s", text_data)
            data = json.loads(text_data)
            logger.info("Parsed JSON data: %s", data)

            organization_id = data.get('organization_id', None)
            logger.info("Extracted organization_id: %s", organization_id)

            assistant_id = data.get('assistant_id', None)

            user = self.scope['user']
            logger.info("Retrieved user from scope: %s", user)

            chat = self.chat
            logger.info("Current chat: %s", chat)
            organization = await self.get_organization(organization_id=organization_id)
            logger.info("Current organization: %s", organization)
            assistant = await self.get_assistant_by_organization(organization=organization)
            logger.info("Current assistant: %s", assistant)
            user_has_active_assistant = await self.user_has_active_assistant(assistant=assistant)
            logger.info("User has active assistant: %s", user_has_active_assistant)

            is_enabled = await self.get_assistant_is_enabled_flag(assistant=assistant)
            logger.info("Chat assistant is enabled: %s", is_enabled)
            comment = await self.handle_item_user_response(data, user)

            if is_enabled:
                logger.info("Chat assistant is enabled.")
                if user_has_active_assistant:
                    if assistant_id is None:
                        logger.info("Assistant ID is None.")
                        await self.send_message_to_item_ai(comment)
                        logger.info("Sent message to AI.")
                    else:
                        logger.info("Assistant ID is provided.")
                        await self.handle_item_ai_response(data, user)
                        logger.info("Handled AI response.")
        except Exception as e:
            logger.error(f"Error in receive: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message'], ensure_ascii=False))



    @database_sync_to_async
    def get_chat_item(self, chat_id):
        return ShopItemService.get(pk=chat_id)

    @database_sync_to_async
    def get_item_with_parent(self, parent):
        return parent.item

    @database_sync_to_async
    def get_assistant_is_enabled_flag(self, assistant):
        return assistant.is_enabled

    @database_sync_to_async
    def get_organization(self, organization_id):
        return OrganizationService.get(id=organization_id)

    @database_sync_to_async
    def get_assistant_by_organization(self, organization):
        if hasattr(organization, 'assistant'):
            return organization.assistant
        return None

    @database_sync_to_async
    def user_has_active_assistant(cls, assistant):
        return UserAssistant.objects.filter(assistant=assistant, is_active=True).exists()

    @database_sync_to_async
    def get_assistant(self, assistant_id):
        assistant = AssistantService.get(pk=assistant_id)
        return assistant

    @database_sync_to_async
    def get_comment(self, comment_id):
        return CommentService.get(pk=comment_id)

    @database_sync_to_async
    def create_user_item_comment(self, text, item, user, parent=None):
        return CommentService.create_item_comment(text=text, item=item, user=user, parent=parent)

    @database_sync_to_async
    def create_ai_defualt_comment(self, chat, parent=None):
        return CommentService.create_ws_chat_comment_with_assistant_default_response(chat=chat, parent=parent)

    @database_sync_to_async
    def create_comment_with_ai_response(self, text, chat, assistant, parent=None):
        return CommentService.create_chat_assistant_comment(text=text, chat=chat, assistant=assistant, parent=parent)

    @database_sync_to_async
    def create_item_comment_with_ai_response(self, text, item, assistant, parent=None):
        return CommentService.create_item_assistant_comment(text=text, item=item, assistant=assistant, parent=parent)

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
    def prepare_item_data(self, comment):
        decoded_headers = {k.decode('utf-8'): v.decode('utf-8') for k, v in self.headers}
        item_info = ItemInfoSerializer(comment.item).data
        assistant = comment.item.organization.assistant
        organization_info = CommentService.get_training_data(assistant=assistant)
        data = {
            "assistant_id": assistant.id,
            "parent_id": comment.id,
            "item_id": comment.item.id,
            "message": comment.text,
            "host": self.host,
            # "training_data": CommentService.get_training_data(assistant=comment.chat.assistant),
            "training_data": {
                    "assistant_info": {
                        "organization": assistant.organization.title,
                        "name": assistant.name,
                        "gender": assistant.gender,
                        "position": assistant.position,
                        "is_enabled": assistant.is_enabled
                    },
                    "item_info": item_info,
                    "organization_info": organization_info
                },
            "headers": decoded_headers
        }
        cleaned_data = convert_decimals(data)
        return cleaned_data

    async def handle_item_user_response(self, data, user):
        try:
            text = data.get('message', '')
            parent_id = data.get('parent', None)
            item = self.chat
            parent = await self.get_comment(parent_id) if parent_id else None
            comment = await self.create_user_item_comment(text, item, user, parent)
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

    async def handle_item_ai_response(self, data, user):
        try:
            text = data.get('message', '')
            parent_id = data.get('parent', None)
            assistant_id = data.get('assistant_id', None)
            assistant = await self.get_assistant(assistant_id)
            parent = await self.get_comment(parent_id)
            item = await self.get_item_with_parent(parent)
            comment = await self.create_item_comment_with_ai_response(text, item, assistant, parent)
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

    # async def handle_ai_default_response(self, parent, user):
    #     try:
    #         chat = await self.get_chat_with_parent(parent)
    #         comment = await self.create_ai_defualt_comment(chat, parent)
    #         serialized_data = await self.serialize_assistant_data(comment=comment, user=user)
    #         await self.channel_layer.group_send(
    #             self.chat_group_name,
    #             {
    #                 'type': 'chat_message',
    #                 'message': serialized_data
    #             }
    #         )
    #     except Exception as e:
    #         logger.error(f"Error handling AI response: {e}")

    async def connect_to_item_ai(self):
        try:
            ai_socket = await websockets.connect('ws://161.35.153.151:8081/ws/bot-item/', timeout=5)
            return ai_socket
        except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to connect to AI socket: {e}")
            await self.close()

    async def send_message_to_item_ai(self, comment):
        try:
            if not hasattr(self, 'ai_socket') or self.ai_socket is None or not self.ai_socket.open:
                logger.warning("AI socket not connected. Attempting to reconnect...")
                self.ai_socket = await self.connect_to_item_ai()
                if not self.ai_socket or not self.ai_socket.open:
                    logger.error("Failed to reconnect to AI socket")
                    return

            data = await self.prepare_item_data(comment)
            logger.debug(f"Sending message to AI: {data}")
            await self.ai_socket.send(json.dumps(data))
            logger.info("Message sent to AI successfully")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection to AI closed unexpectedly: {e}")
            await self.reconnect_item_ai_socket()
        except Exception as e:
            logger.error(f"Error sending message to AI: {e}")
            await self.reconnect_item_ai_socket()

    async def reconnect_item_ai_socket(self):
        try:
            logger.info("Attempting to reconnect to AI socket...")
            if hasattr(self, 'ai_socket') and self.ai_socket.open:
                await self.ai_socket.close()
            self.ai_socket = await self.connect_to_item_ai()
        except Exception as e:
            logger.error(f"Failed to reconnect to AI socket: {e}")

    def extract_item_host(self):
        for header in self.scope['headers']:
            if header[0] == b'host':
                return header[1].decode('utf-8')
        return 'default_host'


