import asyncio
import base64
import decimal
import json
import logging
import re
import uuid

from django.core.files.base import ContentFile

import common.services.slack as slack
import websockets
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from shop.serializers.comment_serializers import CommentSerializer, WSCommentSerializer
from shop.serializers.item_serializers import ItemInfoSerializer
from shop.services.assistant_data_service import AssistantDataService
from shop.services.comment_services import CommentService
from shop.services.item_services import ShopItemService
from stock.serializers import ShopItemSizeCountSetSerializer
from shop.models import Chat,Comment
from users.models import User

from organizations.models import Coupon, DiscountCard, UserAssistant,Answer
from organizations.services.assistant_services import (
    AssistantService,
    ChatService,
)
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem 

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
            self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
            self.chat_group_name = f"chat_{self.chat_id}"
            self.headers = self.scope["headers"]
            self.host = self.extract_host()

            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)

            if self.scope["user"].is_authenticated:
                subprotocol = self.scope.get("subprotocol", None)
                (
                    await self.accept(subprotocol=subprotocol)
                    if subprotocol
                    else await self.accept()
                )
            else:
                logger.warning("Unauthorized user attempted to connect.")
                await self.close()

            self.ai_socket = await self.connect_to_ai()

        except Exception as e:
            logger.error(f"Error in connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        if hasattr(self, "ai_socket") and self.ai_socket.open:
            await self.ai_socket.close()

    async def receive(self, text_data):
        try:
            self.chat = await self.get_chat(self.chat_id)
            if not self.chat:
                logger.warning(f"Chat not found for ID {self.chat_id}")
                await self.close()
                return
            
            data = json.loads(text_data)
            user_audio_base64 = data.get("user_audio", None) 
            assistant_id = data.get("assistant_id", None)
            user = self.scope["user"]
            chat = self.chat
            
            assistant = await self.get_assistant_by_chat(chat=chat)
            user_has_active_assistant = await self.user_has_active_assistant(assistant=assistant)
            is_enabled = await self.get_chat_assistant_is_enabled_flag(chat=chat)
            chat_by_org_user = await self.get_chat_chat_org_by_user(chat=chat)

            if is_enabled:
                if chat_by_org_user:
                    await self.handle_user_response(data, user)
                else:
                    if user_has_active_assistant:
                        if assistant_id is None:
                            comment = await self.handle_user_response(data, user)

                            await self.send_message_to_ai_with_audio(comment, user_audio_base64)
                        else:

                            await self.handle_ai_response(data, user)
                    else:
                        await self.handle_user_response(data, user)
            else:
                comment = await self.handle_user_response(data, user)
                await self.handle_ai_default_response(parent=comment, user=user)
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            logger.error(f"Error in receive: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"], ensure_ascii=False))

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
        return UserAssistant.objects.filter(
            assistant=assistant, is_active=True
        ).exists()

    @database_sync_to_async
    def get_assistant(self, assistant_id):
        assistant = AssistantService.get(pk=assistant_id)
        return assistant

    @database_sync_to_async
    def get_comment(self, comment_id):
        return CommentService.get(pk=comment_id)

    @database_sync_to_async
    def create_user_comment(self, text, chat, user, parent=None):
        return CommentService.create_chat_comment(
            text=text, chat=chat, user=user, parent=parent
        )

    @database_sync_to_async
    def create_ai_defualt_comment(self, chat, parent=None):
        return CommentService.create_ws_chat_comment_with_assistant_default_response(
            chat=chat, parent=parent
        )

    @database_sync_to_async
    def create_comment_with_ai_response(self, text, chat, assistant, parent=None, audio_base64=None):
        audio_file = None
        if audio_base64:
            try:
                decoded_file = base64.b64decode(audio_base64)
                file_name = f"voice_{uuid.uuid4()}.mp3"
                audio_file = ContentFile(decoded_file, name=file_name)
            except Exception as e:
                logger.error(f"Error decoding audio base64: {e}")
        return CommentService.create_chat_assistant_comment(
            text=text, chat=chat, assistant=assistant, parent=parent, audio_file=audio_file
        )

    @database_sync_to_async
    def serialize_data(self, comment, user):
        fake_request = type("FakeRequest", (object,), {"user": user})()
        serializer = CommentSerializer(comment, context={"request": fake_request})
        return serializer.data

    @database_sync_to_async
    def serialize_assistant_data(self, comment, user):
        serializer = WSCommentSerializer(comment, context={"user": user})
        return serializer.data

    @database_sync_to_async
    def get_chat_history(self, chat, limit: int = 5):
        """
        Get last N message pairs from chat for context.
        Returns list of dicts with role and content.
        """
        from shop.models import Comment

        # Get last N*2 messages (pairs of user + assistant)
        messages = Comment.objects.filter(chat=chat).order_by("-created_at")[
            : limit * 2
        ]
        messages = list(reversed(messages))  # Chronological order

        history = []
        for msg in messages:
            role = "assistant" if msg.assistant else "user"
            history.append(
                {
                    "role": role,
                    "content": msg.text,
                }
            )
        return history

    @database_sync_to_async
    def prepare_data(self, comment):
        decoded_headers = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in self.headers
        }

        # Get training data
        training_data = CommentService.get_training_data(
            assistant=comment.chat.assistant
        )

        # Add chat history for context (last 5 pairs = 10 messages)
        from shop.models import Comment as CommentModel

        messages = (
            CommentModel.objects.filter(chat=comment.chat)
            .exclude(id=comment.id)
            .order_by("-created_at")[:10]
        )
        messages = list(reversed(messages))

        chat_history = []
        for msg in messages:
            role = "assistant" if msg.assistant else "user"
            chat_history.append(
                {
                    "role": role,
                    "content": msg.text,
                }
            )

        training_data["chat_history"] = chat_history

        data = {
            "assistant_id": comment.chat.assistant.id,
            "parent_id": comment.id,
            "chat_id": comment.chat.id,
            "message": comment.text,
            "host": self.host,
            "training_data": training_data,
            "headers": decoded_headers,
        }
        return data

    async def send_message_to_ai_with_audio(self, comment, audio_base64):
        try:
            if not hasattr(self, "ai_socket") or not self.ai_socket.open:
                self.ai_socket = await self.connect_to_ai()


            data = await self.prepare_data(comment)

            data["user_audio"] = audio_base64 
            
            await self.ai_socket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending to AI: {e}")
    
    @database_sync_to_async
    def create_user_comment_with_audio(self, text, chat, user, audio_base64=None, parent=None):
        user_audio_file = None
        if audio_base64:
            try:
                if ";base64," in audio_base64:
                    header, audio_base64 = audio_base64.split(";base64,")

                decoded_file = base64.b64decode(audio_base64)
                file_name = f"user_voice_{uuid.uuid4()}.mp3"
                user_audio_file = ContentFile(decoded_file, name=file_name)
            except Exception as e:
                logger.error(f"Error decoding user audio: {e}")

        return CommentService.create_chat_comment(
            text=text or "[Голосовое сообщение]", 
            chat=chat, 
            user=user, 
            parent=parent,
            user_audio_file=user_audio_file
        )


    async def handle_user_response(self, data, user):

        try:
            text = data.get("message", "")
            parent_id = data.get("parent", None)
            audio_base64 = data.get("user_audio") 
            chat = self.chat
            parent = await self.get_comment(parent_id) if parent_id else None
            
            comment = await self.create_user_comment_with_audio(text, chat, user, audio_base64, parent)
            
            serialized_data = await self.serialize_data(comment=comment, user=user)
            await self.channel_layer.group_send(
                self.chat_group_name,
                {"type": "chat_message", "message": serialized_data},
            )
            return comment
        except Exception as e:
            logger.error(f"Error handling user response: {e}")

    async def handle_ai_response(self, data, user):
        try:
            text = data.get("message", "")
            audio_base64 = data.get("audio", None)
            parent_id = data.get("parent", None)
            assistant_id = data.get("assistant_id", None)
            assistant = await self.get_assistant(assistant_id)
            parent = await self.get_comment(parent_id)
            chat = await self.get_chat_with_parent(parent)


            comment = await self.create_comment_with_ai_response(
                text, chat, assistant, parent, audio_base64
            )
            serialized_data = await self.serialize_assistant_data(
                comment=comment, user=user
            )


            # match = re.search(r'/p/(\d+)', text)
            # if match:
            #     item_id = match.group(1)
            #     logger.info(f"Found Item ID in AI response: {item_id}")
            #
            #     image_url = await self.get_item_image_url(item_id)
            #
            #     if image_url:
            #
            #         serialized_data['product_image'] = image_url
            #         logger.info(f"Attached image to response: {image_url}")


            await self.channel_layer.group_send(
                self.chat_group_name,
                {"type": "chat_message", "message": serialized_data},
            )
        except Exception as e:
            logger.error(f"Error handling AI response: {e}")
            slack.slack_ai(f"[ WEBSOCKET error ] error handling AI response: {e}")
    
    # @database_sync_to_async
    # def get_item_image_url(self, item_id):
    #
    #     try:
    #         item = ShopItem.objects.filter(id=item_id).first()
    #
    #         if not item:
    #             return None
    #
    #         first_image = item.images.all().order_by('order').first()
    #         if first_image:
    #             return first_image.medium_property
    #
    #         first_video = item.videos.all().order_by('order').first()
    #         if first_video and first_video.thumbnail:
    #             return first_video.thumbnail.medium_property
    #
    #         return None
    #
    #     except Exception as e:
    #         logger.error(f"Error fetching image for item {item_id}: {e}")
    #         return None

    async def handle_ai_default_response(self, parent, user):
        try:
            chat = await self.get_chat_with_parent(parent)
            comment = await self.create_ai_defualt_comment(chat, parent)
            serialized_data = await self.serialize_assistant_data(
                comment=comment, user=user
            )
            await self.channel_layer.group_send(
                self.chat_group_name,
                {"type": "chat_message", "message": serialized_data},
            )
        except Exception as e:
            logger.error(f"Error handling AI response: {e}")
            slack.slack_ai(f"[ WEBSOCKET error ] error handling AI response: {e}")

    async def connect_to_ai(self):
        try:
            ai_socket = await websockets.connect(
                "ws://161.35.153.151:8081/ws/bot/", timeout=5
            )
            slack.slack_ai("[ WEBSOCKET logs ] connecting to AI socket")
            return ai_socket
        except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to connect to AI socket: {e}")
            slack.slack_ai(
                f"[ WEBSOCKET error ] connection failed while attempt to AI socket {e}"
            )
            await self.close()

    async def send_message_to_ai(self, comment):
        try:
            if (
                not hasattr(self, "ai_socket")
                or self.ai_socket is None
                or not self.ai_socket.open
            ):
                logger.warning("AI socket not connected. Attempting to reconnect...")
                self.ai_socket = await self.connect_to_ai()
                if not self.ai_socket or not self.ai_socket.open:
                    logger.error("Failed to reconnect to AI socket")
                    slack.slack_ai(
                        "[ WEBSOCKET error ] reconnection failed to AI socket"
                    )
                    return

            data = await self.prepare_data(comment)
            logger.info(f"Sending message to AI: {data}")
            await self.ai_socket.send(json.dumps(data))
            logger.info("Message sent to AI successfully")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Connection to AI closed unexpectedly: {e}")
            slack.slack_ai(f"[ WEBSOCKET error ] connection to AI closed: {e}")
            await self.reconnect_ai_socket()
        except Exception as e:
            logger.error(f"Error sending message to AI: {e}")
            slack.slack_ai(f"[ WEBSOCKET error ] error sending message to AI: {e}")
            await self.reconnect_ai_socket()

    async def reconnect_ai_socket(self):
        try:
            logger.info("Attempting to reconnect to AI socket...")
            if hasattr(self, "ai_socket") and self.ai_socket.open:
                await self.ai_socket.close()
            self.ai_socket = await self.connect_to_ai()
        except Exception as e:
            logger.error(f"Failed to reconnect to AI socket: {e}")
            slack.slack_ai(f"[ WEBSOCKET error ] failed reconnecting to AI socket: {e}")

    def extract_host(self):
        for header in self.scope["headers"]:
            if header[0] == b"host":
                return header[1].decode("utf-8")
        return "default_host"


class CommentItemConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
            self.chat_group_name = f"chat_{self.chat_id}"
            self.headers = self.scope["headers"]
            self.host = self.extract_item_host()

            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)

            if self.scope["user"].is_authenticated:
                subprotocol = self.scope.get("subprotocol", None)
                (
                    await self.accept(subprotocol=subprotocol)
                    if subprotocol
                    else await self.accept()
                )
            else:
                logger.warning("Unauthorized user attempted to connect.")
                await self.close()

            self.ai_socket = await self.connect_to_item_ai()

        except Exception as e:
            logger.error(f"Error in connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        if hasattr(self, "ai_socket") and self.ai_socket.open:
            await self.ai_socket.close()

    async def receive(self, text_data):
        try:
            logger.info("Received text data: %s", text_data)
            self.chat = await self.get_chat_item(self.chat_id)
            if not self.chat:
                logger.warning(f"Chat not found for ID {self.chat_id}")
                await self.close()
                return
            logger.info("Received text data: %s", text_data)
            data = json.loads(text_data)
            logger.info("Parsed JSON data: %s", data)
            user = self.scope["user"]
            logger.info("Retrieved user from scope: %s", user)
            chat = self.chat
            logger.info("Current chat: %s", chat)

            organization_id = data.get("organization_id", None)
            if organization_id is not None:
                comment = await self.handle_item_user_response(data, user)
                logger.info("Extracted organization_id: %s", organization_id)
                organization = await self.get_organization(
                    organization_id=organization_id
                )
                logger.info("Current organization: %s", organization)
                assistant = await self.get_assistant_by_organization(
                    organization=organization
                )
                logger.info("Current assistant: %s", assistant)
                user_has_active_assistant = await self.user_has_active_assistant(
                    assistant=assistant
                )
                logger.info("User has active assistant: %s", user_has_active_assistant)
                is_enabled = await self.get_assistant_is_enabled_flag(
                    assistant=assistant
                )
                logger.info("Chat assistant is enabled: %s", is_enabled)
                if is_enabled:
                    logger.info("Chat assistant is enabled.")
                    if user_has_active_assistant:
                        await self.send_message_to_item_ai(comment)
                        logger.info("Sent message to AI.")

            assistant_id = data.get("assistant_id", None)
            if assistant_id is not None:
                logger.info("Assistant ID is provided.")
                await self.handle_item_ai_response(data, user)
                logger.info("Handled AI response.")
        except Exception as e:
            logger.error(f"Error in receive: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"], ensure_ascii=False))

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
        if hasattr(organization, "assistant"):
            return organization.assistant
        return None

    @database_sync_to_async
    def user_has_active_assistant(cls, assistant):
        return UserAssistant.objects.filter(
            assistant=assistant, is_active=True
        ).exists()

    @database_sync_to_async
    def get_assistant(self, assistant_id):
        assistant = AssistantService.get(pk=assistant_id)
        return assistant

    @database_sync_to_async
    def get_comment(self, comment_id):
        return CommentService.get(pk=comment_id)

    @database_sync_to_async
    def create_user_item_comment(self, text, item, user, parent=None):
        return CommentService.create_item_comment(
            text=text, item=item, user=user, parent=parent
        )

    @database_sync_to_async
    def create_ai_defualt_comment(self, chat, parent=None):
        return CommentService.create_ws_chat_comment_with_assistant_default_response(
            chat=chat, parent=parent
        )

    @database_sync_to_async
    def create_comment_with_ai_response(self, text, chat, assistant, parent=None):
        return CommentService.create_chat_assistant_comment(
            text=text, chat=chat, assistant=assistant, parent=parent
        )

    @database_sync_to_async
    def create_item_comment_with_ai_response(self, text, item, assistant, parent=None):
        return CommentService.create_item_assistant_comment(
            text=text, item=item, assistant=assistant, parent=parent
        )

    @database_sync_to_async
    def serialize_data(self, comment, user):
        fake_request = type("FakeRequest", (object,), {"user": user})()
        serializer = CommentSerializer(comment, context={"request": fake_request})
        return serializer.data

    @database_sync_to_async
    def serialize_assistant_data(self, comment, user):
        serializer = WSCommentSerializer(comment, context={"user": user})
        return serializer.data

    @database_sync_to_async
    def prepare_item_data(self, comment):
        decoded_headers = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in self.headers
        }

        org = comment.item.organization
        item_info = ItemInfoSerializer(comment.item).data
        assistant = comment.item.organization.assistant
        answers = Answer.objects.filter(assistant=assistant)
        # organization_info = CommentService.get_training_data(assistant=assistant)
        organization_info = {
            "name": org.title,
            "description": org.description or "",
            "address": org.address or "",
            "opens_at": str(org.opens_at) if org.opens_at else "",
            "closes_at": str(org.closes_at) if org.closes_at else "",
        }

        phone_numbers = list(org.phone_numbers.values_list("phone_number", flat=True))
        if phone_numbers:
            organization_info["phones"] = ", ".join(phone_numbers)

        social_contacts = list(org.social_contacts.values_list("url", flat=True))

        if social_contacts:
            organization_info["social_links"] = ", ".join(social_contacts)
        size_info = comment.item.shop_item_size_counts.all()
        stock_info = ShopItemSizeCountSetSerializer(
            size_info, many=True, context={"request": None}
        ).data

        catalog_url = AssistantDataService.get_file_url(org)
        org_url = f"{settings.SITE_URL}/organizations/{org.id}"

        marketing_info = []
        discounts = DiscountCard.objects.filter(organization=org, is_published=True)
        coupons = Coupon.objects.filter(organization=org, is_active=True)
        coupons_info = []
        for coupon in coupons:
            coupons_info.append(f"{coupon.percent} - {coupon.description}")

        for card in discounts:
            if card.type == DiscountCard.FIXED:
                marketing_info.append(f"Постоянная скидка: {card.percent}%")

            elif card.type == DiscountCard.CASHBACK:
                marketing_info.append(f"Кэшбек: {card.percent}%")

            elif card.type == DiscountCard.CUMULATIVE:
                limit_str = (
                    f"{card.limit} {card.currency.code}"
                    if card.limit and card.currency
                    else "определенной суммы"
                )
                marketing_info.append(
                    f"Накопительная скидка {card.percent}% (при покупках от {limit_str})"
                )

        # Add chat history for item comments (last 10 messages)
        from shop.models import Comment as CommentModel

        item_messages = (
            CommentModel.objects.filter(item=comment.item)
            .exclude(id=comment.id)
            .order_by("-created_at")[:10]
        )
        item_messages = list(reversed(item_messages))

        chat_history = []
        for msg in item_messages:
            role = "assistant" if msg.assistant else "user"
            chat_history.append(
                {
                    "role": role,
                    "content": msg.text,
                }
            )

        data = {
            "assistant_id": assistant.id,
            "parent_id": comment.id,
            "item_id": comment.item.id,
            "message": comment.text,
            "host": self.host,
            "training_data": {
                "assistant_info": {
                    "organization": assistant.organization.title,
                    "name": assistant.name,
                    "gender": assistant.gender,
                    "position": assistant.position,
                    "is_enabled": assistant.is_enabled,
                    "ai_prompt": assistant.ai_prompt,
                    "first_message": assistant.first_message,
                    "ai_voice": assistant.ai_voice,
                },
                "answers": [],
                "item_info": item_info,
                "organization_info": organization_info,
                "stock_info": stock_info,
                "catalog_file": catalog_url,
                "organization_page_url": org_url,
                "marketing_info": marketing_info,
                "coupons_info": coupons_info,
                "chat_history": chat_history,
            },
            "headers": decoded_headers,
        }
        cleaned_data = convert_decimals(data)
        return cleaned_data

    async def handle_item_user_response(self, data, user):
        try:
            text = data.get("message", "")
            parent_id = data.get("parent", None)
            item = self.chat
            parent = await self.get_comment(parent_id) if parent_id else None
            comment = await self.create_user_item_comment(text, item, user, parent)
            serialized_data = await self.serialize_data(comment=comment, user=user)
            await self.channel_layer.group_send(
                self.chat_group_name,
                {"type": "chat_message", "message": serialized_data},
            )
            return comment
        except Exception as e:
            logger.error(f"Error handling user response: {e}")

    async def handle_item_ai_response(self, data, user):
        try:
            text = data.get("message", "")
            parent_id = data.get("parent", None)
            assistant_id = data.get("assistant_id", None)
            assistant = await self.get_assistant(assistant_id)
            parent = await self.get_comment(parent_id)
            item = await self.get_item_with_parent(parent)
            comment = await self.create_item_comment_with_ai_response(
                text, item, assistant, parent
            )
            serialized_data = await self.serialize_assistant_data(
                comment=comment, user=user
            )
            await self.channel_layer.group_send(
                self.chat_group_name,
                {"type": "chat_message", "message": serialized_data},
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
            ai_socket = await websockets.connect(
                "ws://161.35.153.151:8081/ws/bot-item/", timeout=5
            )
            return ai_socket
        except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to connect to AI socket: {e}")
            await self.close()

    async def send_message_to_item_ai(self, comment):
        try:
            if (
                not hasattr(self, "ai_socket")
                or self.ai_socket is None
                or not self.ai_socket.open
            ):
                logger.warning("AI socket not connected. Attempting to reconnect...")
                self.ai_socket = await self.connect_to_item_ai()
                if not self.ai_socket or not self.ai_socket.open:
                    logger.error("Failed to reconnect to AI socket")
                    return

            data = await self.prepare_item_data(comment)
            logger.info(f"Sending message to AI: {data}")
            await self.ai_socket.send(json.dumps(data))
            logger.info("Message sent to AI successfully")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Connection to AI closed unexpectedly: {e}")
            await self.reconnect_item_ai_socket()
        except Exception as e:
            logger.error(f"Error sending message to AI: {e}")
            await self.reconnect_item_ai_socket()

    async def reconnect_item_ai_socket(self):
        try:
            logger.info("Attempting to reconnect to AI socket...")
            if hasattr(self, "ai_socket") and self.ai_socket.open:
                await self.ai_socket.close()
            self.ai_socket = await self.connect_to_item_ai()
        except Exception as e:
            logger.error(f"Failed to reconnect to AI socket: {e}")

    def extract_item_host(self):
        for header in self.scope["headers"]:
            if header[0] == b"host":
                return header[1].decode("utf-8")
        return "default_host"
