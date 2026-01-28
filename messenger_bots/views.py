import json
import logging
import hmac
import hashlib
import re
from typing import Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from messenger_bots.models import (
    TelegramBot,
    WhatsAppBot,
    WhatsAppProvider,
    WhatsAppSessionStatus,
    BotChat,
    BotMessage,
    BotPlatform,
    BotCreationRequest,
    BotCreationStatus,
    TelegramUserbot,
)
from messenger_bots.services import TelegramBotService, WhatsAppBotService
from messenger_bots.services.whatsapp import WhatsAppServiceFactory
from messenger_bots.serializers import (
    TelegramBotSerializer,
    TelegramBotCreateSerializer,
    WhatsAppBotSerializer,
    WhatsAppBotCreateSerializer,
    WhatsAppBotWAHACreateSerializer,
    WhatsAppSessionStatusSerializer,
    BotChatSerializer,
    BotMessageSerializer,
    BotCreationRequestSerializer,
)
from organizations.models import Organization

logger = logging.getLogger(__name__)


def _sync_linked_chat_waha(bot_chat: BotChat, organization) -> None:
    """Sync BotChat with organizations.Chat for unified chat list (WAHA WhatsApp)."""
    from django.db.models import F
    from organizations.models import Assistant, Chat, ChatSource

    try:
        assistant = Assistant.objects.filter(organization=organization).first()
        if not assistant:
            return

        linked_chat, created = Chat.objects.get_or_create(
            bot_chat=bot_chat,
            defaults={
                'assistant': assistant,
                'source': ChatSource.WHATSAPP,
                'user': None,
                'is_read': False,
                'unread_count': 1,
            }
        )

        if not created:
            Chat.objects.filter(id=linked_chat.id).update(
                unread_count=F('unread_count') + 1,
                is_read=False
            )
    except Exception as e:
        logger.error(f"[WAHA] Error syncing linked chat: {e}", exc_info=True)


def _send_ws_notification_waha(bot_message: BotMessage, bot_chat: BotChat) -> None:
    """Send WebSocket notification for WAHA WhatsApp message."""
    from shop.serializers.comment_serializers import BotMessageSerializer

    try:
        linked_chat = getattr(bot_chat, 'linked_chat', None)
        if not linked_chat:
            return

        chat_group_name = f"chat_{linked_chat.id}"
        serialized_data = BotMessageSerializer(bot_message).data

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                chat_group_name,
                {"type": "chat_message", "message": serialized_data}
            )
    except Exception as e:
        logger.error(f"[WAHA] Error sending WS notification: {e}", exc_info=True)


# ============== Webhook Views (No Auth Required) ==============

@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """Handle incoming Telegram webhook updates."""

    def post(self, request, organization_id):
        logger.info(f"[TG_WEBHOOK] Received webhook for org_id={organization_id}")
        logger.debug(f"[TG_WEBHOOK] Headers: {dict(request.headers)}")

        try:
            # Get bot
            telegram_bot = TelegramBot.objects.select_related("organization").get(
                organization_id=organization_id,
                is_active=True,
            )
            logger.info(f"[TG_WEBHOOK] Found bot: @{telegram_bot.bot_username} for org '{telegram_bot.organization.title}'")
        except TelegramBot.DoesNotExist:
            logger.error(f"[TG_WEBHOOK] ERROR: Bot not found or inactive for org_id={organization_id}")
            return HttpResponse(status=404)

        # Verify secret token
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_token != telegram_bot.webhook_secret:
            logger.error(f"[TG_WEBHOOK] ERROR: Invalid secret token for org_id={organization_id}. Expected: {telegram_bot.webhook_secret[:10]}..., Got: {secret_token[:10] if secret_token else 'None'}...")
            return HttpResponse(status=403)

        # Parse update
        try:
            update = json.loads(request.body)
            logger.info(f"[TG_WEBHOOK] Update parsed. update_id={update.get('update_id')}")
            logger.debug(f"[TG_WEBHOOK] Full update: {json.dumps(update, ensure_ascii=False)[:500]}")
        except json.JSONDecodeError as e:
            logger.error(f"[TG_WEBHOOK] ERROR: Invalid JSON in request body: {e}")
            return HttpResponse(status=400)

        # Extract message info for logging
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        from_user = message.get("from", {})
        text = message.get("text", "")[:100]  # First 100 chars
        logger.info(f"[TG_WEBHOOK] Message from chat_id={chat_id}, user_id={from_user.get('id')}, username=@{from_user.get('username')}, text='{text}'")

        # Process update asynchronously (in production, use Celery)
        try:
            logger.info(f"[TG_WEBHOOK] Processing update with TelegramBotService...")
            TelegramBotService.process_webhook_update(telegram_bot, update)
            logger.info(f"[TG_WEBHOOK] Update processed successfully")
        except Exception as e:
            logger.error(f"[TG_WEBHOOK] ERROR processing update: {e}", exc_info=True)

        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(View):
    """Handle incoming WhatsApp webhook updates."""

    def get(self, request, organization_id):
        """Webhook verification (called by Meta during setup)."""
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode != "subscribe":
            return HttpResponse(status=400)

        try:
            whatsapp_bot = WhatsAppBot.objects.get(
                organization_id=organization_id,
            )
        except WhatsAppBot.DoesNotExist:
            return HttpResponse(status=404)

        if token == whatsapp_bot.verify_token:
            return HttpResponse(challenge, status=200)

        return HttpResponse(status=403)

    def post(self, request, organization_id):
        """Handle incoming messages."""
        try:
            whatsapp_bot = WhatsAppBot.objects.select_related("organization").get(
                organization_id=organization_id,
                is_active=True,
            )
        except WhatsAppBot.DoesNotExist:
            logger.warning(f"WhatsApp webhook for unknown org: {organization_id}")
            return HttpResponse(status=404)

        # Verify signature (optional but recommended)
        signature = request.headers.get("X-Hub-Signature-256", "")
        if whatsapp_bot.webhook_secret:
            if not WhatsAppBotService.verify_webhook_signature(
                whatsapp_bot, request.body, signature
            ):
                logger.warning(f"Invalid WhatsApp webhook signature for org: {organization_id}")
                return HttpResponse(status=403)

        # Parse update
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        # Process update
        try:
            WhatsAppBotService.process_webhook_update(whatsapp_bot, data)
        except Exception as e:
            logger.error(f"Error processing WhatsApp update: {e}")

        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name="dispatch")
class WAHAWebhookView(View):
    """Handle incoming WAHA (WhatsApp HTTP API) webhook updates.

    WAHA sends webhooks globally (not per-organization), so we extract
    the organization ID from the session name (e.g., "org_123").
    """

    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify HMAC-SHA512 signature from WAHA."""
        secret = getattr(settings, "WAHA_WEBHOOK_SECRET", "")

        # Debug logging
        logger.info(f"WAHA webhook signature verification: signature_present={bool(signature)}, secret_configured={bool(secret)}")

        if not signature:
            # If no signature provided, allow for now (WAHA session might not have HMAC configured)
            logger.warning("WAHA webhook: No signature provided, allowing request")
            return True

        if not secret:
            # If no secret configured, skip verification
            logger.warning("WAHA_WEBHOOK_SECRET not configured, skipping signature verification")
            return True

        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha512
        ).hexdigest()

        is_valid = hmac.compare_digest(expected, signature)
        if not is_valid:
            logger.warning(f"WAHA webhook signature mismatch: expected={expected[:20]}..., got={signature[:20]}...")

        return is_valid

    # ============== WAHA PLUS VERSION CODE (uncomment when upgraded) ==============
    # def _extract_org_id_from_session(self, session_name: str) -> Optional[int]:
    #     """Extract organization ID from session name (e.g., 'org_123' -> 123)."""
    #     if not session_name:
    #         return None
    #     match = re.match(r"^org_(\d+)$", session_name)
    #     if match:
    #         return int(match.group(1))
    #     return None
    # ============== END WAHA PLUS VERSION CODE ==============

    def _find_bot_by_session(self, session_name: str) -> Optional[WhatsAppBot]:
        """Find WhatsApp bot by session name.

        WAHA Core (free): only supports 'default' session (1 WhatsApp per instance)
        WAHA Plus: supports multiple sessions like 'org_123'

        When upgrading to WAHA Plus:
        1. Change waha.py: session_name = f"org_{whatsapp_bot.organization_id}"
        2. Uncomment _extract_org_id_from_session above
        3. Update this method to use org_id extraction first
        """
        if not session_name:
            return None

        # WAHA Plus: Try to extract org_id from session name (e.g., 'org_123' -> 123)
        match = re.match(r"^org_(\d+)$", session_name)
        if match:
            org_id = int(match.group(1))
            try:
                return WhatsAppBot.objects.select_related("organization").get(
                    organization_id=org_id,
                    provider=WhatsAppProvider.WAHA,
                    is_active=True,
                )
            except WhatsAppBot.DoesNotExist:
                return None

        # WAHA Core: For 'default' session - find by waha_session_name or first active bot
        try:
            return WhatsAppBot.objects.select_related("organization").get(
                waha_session_name=session_name,
                provider=WhatsAppProvider.WAHA,
                is_active=True,
            )
        except WhatsAppBot.DoesNotExist:
            pass

        # Fallback for 'default' session - find first active WAHA bot
        if session_name == "default":
            return WhatsAppBot.objects.select_related("organization").filter(
                provider=WhatsAppProvider.WAHA,
                is_active=True,
            ).first()

        return None

    def post(self, request):
        """Handle incoming WAHA webhook events."""
        # Verify signature (WAHA sends X-Webhook-Hmac-Sha512 header)
        signature = request.headers.get("X-Webhook-Hmac-Sha512", "")
        if not self._verify_signature(request.body, signature):
            logger.warning("Invalid WAHA webhook signature")
            return HttpResponse(status=403)

        # Parse payload
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in WAHA webhook")
            return HttpResponse(status=400)

        # Extract session name and event type
        session_name = data.get("session", "")
        event_type = data.get("event", "")

        logger.info(f"WAHA webhook: event={event_type}, session={session_name}")

        # Find WhatsApp bot by session name
        whatsapp_bot = self._find_bot_by_session(session_name)

        # Check if this message should be routed to OTP/Voice bot
        # For 'default' session: route to OTP bot if sender is not in org's BotChat
        if session_name == "default" and event_type == "message" and whatsapp_bot:
            payload = data.get("payload", {})
            # Skip outgoing messages
            if not payload.get("fromMe", False):
                # Extract phone number from message
                from_number = payload.get("from", "")
                _data = payload.get("_data", {})
                key_data = _data.get("key", {})
                remote_jid_alt = key_data.get("remoteJidAlt", "")

                if remote_jid_alt and "@s.whatsapp.net" in remote_jid_alt:
                    phone_number = remote_jid_alt.replace("@s.whatsapp.net", "")
                elif "@" in from_number:
                    phone_number = from_number.split("@")[0]
                else:
                    phone_number = from_number

                # Check if this phone has existing chat with organization
                existing_chat = BotChat.objects.filter(
                    organization=whatsapp_bot.organization,
                    platform=BotPlatform.WHATSAPP,
                    platform_chat_id=phone_number,
                ).exists()

                if not existing_chat:
                    # New user - route to OTP/Voice bot handler
                    logger.info(f"WAHA webhook: routing NEW user {phone_number[:7]}*** to OTP bot handler")
                    try:
                        from otp_bot.webhook_handler import OTPBotWebhookHandler
                        handler = OTPBotWebhookHandler()
                        handler.handle(data)  # Method is 'handle', not 'handle_webhook'
                    except Exception as e:
                        logger.error(f"WAHA webhook: OTP bot handler error: {e}", exc_info=True)
                    return HttpResponse(status=200)
        if not whatsapp_bot:
            logger.warning(f"WAHA webhook: no bot found for session '{session_name}'")
            return HttpResponse(status=200)  # Return 200 to avoid retries

        # Update last activity
        whatsapp_bot.last_activity_at = timezone.now()

        # Handle different event types
        if event_type == "session.status":
            self._handle_session_status(whatsapp_bot, data)
        elif event_type == "message":
            self._handle_message(whatsapp_bot, data)
        elif event_type == "message.ack":
            self._handle_message_ack(whatsapp_bot, data)
        elif event_type == "message.reaction":
            pass  # Ignore reactions for now
        else:
            logger.debug(f"Unhandled WAHA event type: {event_type}")

        whatsapp_bot.save(update_fields=["last_activity_at"])

        return HttpResponse(status=200)

    def _handle_session_status(self, whatsapp_bot: WhatsAppBot, data: dict):
        """Handle session status changes (QR code, connected, disconnected)."""
        payload = data.get("payload", {})
        status_name = payload.get("status", "")

        logger.info(f"WAHA session status for org {whatsapp_bot.organization_id}: {status_name}")

        status_mapping = {
            "STARTING": WhatsAppSessionStatus.PENDING,
            "SCAN_QR_CODE": WhatsAppSessionStatus.SCAN_QR,
            "WORKING": WhatsAppSessionStatus.AUTHENTICATED,
            "STOPPED": WhatsAppSessionStatus.DISCONNECTED,
            "FAILED": WhatsAppSessionStatus.FAILED,
        }

        new_status = status_mapping.get(status_name)
        if new_status:
            whatsapp_bot.session_status = new_status

            # If authenticated, try to get the connected phone number
            if new_status == WhatsAppSessionStatus.AUTHENTICATED:
                # Phone number will be extracted from 'me' webhook or API call
                pass

        whatsapp_bot.save(update_fields=["session_status"])

    def _handle_message(self, whatsapp_bot: WhatsAppBot, data: dict):
        """Handle incoming message."""
        payload = data.get("payload", {})

        # Skip outgoing messages (messages sent by us)
        if payload.get("fromMe", False):
            return

        # Extract message details
        from_number = payload.get("from", "")
        message_body = payload.get("body", "")
        message_id = payload.get("id", {}).get("id", "") if isinstance(payload.get("id"), dict) else payload.get("id", "")
        timestamp = payload.get("timestamp")

        # WAHA uses LID (Linked ID) format like "230545808167055@lid"
        # The actual phone number is in _data.key.remoteJidAlt like "996550022578@s.whatsapp.net"
        # We need to extract the real phone number for sending replies
        _data = payload.get("_data", {})
        key_data = _data.get("key", {})
        remote_jid_alt = key_data.get("remoteJidAlt", "")

        # Try to get real phone number from remoteJidAlt first
        if remote_jid_alt and "@s.whatsapp.net" in remote_jid_alt:
            phone_number = remote_jid_alt.replace("@s.whatsapp.net", "")
            logger.debug(f"WAHA: Using remoteJidAlt phone: {phone_number}")
        elif "@" in from_number:
            # Fallback to from field (remove any suffix)
            phone_number = from_number.split("@")[0]
            logger.debug(f"WAHA: Using from field: {phone_number}")
        else:
            phone_number = from_number

        if not phone_number or not message_body:
            logger.debug(f"Skipping empty message from {from_number}")
            return

        # Extract user name from pushName if available
        push_name = _data.get("pushName", "")

        # Get or create chat
        chat, created = BotChat.objects.get_or_create(
            organization=whatsapp_bot.organization,
            platform=BotPlatform.WHATSAPP,
            platform_chat_id=phone_number,
            defaults={
                "user_phone": phone_number,
                "platform_user_id": phone_number,
                "user_name": push_name or None,
            }
        )

        # Update user name if we have it now and didn't before
        update_fields = ["last_message_at"]
        chat.last_message_at = timezone.now()
        if push_name and not chat.user_name:
            chat.user_name = push_name
            update_fields.append("user_name")

        # Fetch profile picture if not yet available
        if created or not chat.user_photo:
            try:
                service = WhatsAppServiceFactory.get_service(whatsapp_bot)
                profile_picture_url = service.get_profile_picture(phone_number)
                if profile_picture_url:
                    chat.user_photo = profile_picture_url
                    update_fields.append("user_photo")
                    logger.debug(f"WAHA: Profile picture saved for {phone_number}")
            except Exception as e:
                logger.debug(f"WAHA: Failed to get profile picture: {e}")

        chat.save(update_fields=update_fields)

        # Save incoming message
        incoming_msg = BotMessage.objects.create(
            chat=chat,
            sender=BotMessage.USER,
            text=message_body,
            platform_message_id=message_id,
        )

        # Sync with organizations.Chat for unified chat list
        _sync_linked_chat_waha(chat, whatsapp_bot.organization)

        # Send WebSocket notification for incoming message
        _send_ws_notification_waha(incoming_msg, chat)

        logger.info(f"WAHA message from {phone_number} to org {whatsapp_bot.organization_id}: {message_body[:50]}...")

        # Process with AI assistant (async task)
        from messenger_bots.tasks import process_whatsapp_message_task
        process_whatsapp_message_task.delay(
            whatsapp_bot_id=whatsapp_bot.id,
            chat_id=chat.id,
            message_text=message_body,
            is_first_message=created,  # Send welcome if new chat
        )

    def _handle_message_ack(self, whatsapp_bot: WhatsAppBot, data: dict):
        """Handle message acknowledgment (delivered, read)."""
        # For now, just log it
        payload = data.get("payload", {})
        ack_status = payload.get("ack")
        logger.debug(f"WAHA message ack for org {whatsapp_bot.organization_id}: {ack_status}")


# ============== API Views (Auth Required) ==============

class TelegramBotAPIView(APIView):
    """API for managing Telegram bot configuration."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        logger.debug(f"[TG_API] get_organization: org_id={organization_id}, user_id={request.user.id}")
        try:
            org = Organization.objects.get(id=organization_id)
            # Check if user is owner or has permission
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    logger.warning(f"[TG_API] Access denied: user {request.user.id} is not owner/editor of org {organization_id}")
                    return None
            logger.debug(f"[TG_API] Organization found: '{org.title}' (id={org.id})")
            return org
        except Organization.DoesNotExist:
            logger.warning(f"[TG_API] Organization not found: id={organization_id}")
            return None

    def get(self, request, organization_id):
        """Get Telegram bot configuration."""
        logger.info(f"[TG_API] GET bot config for org_id={organization_id}, user={request.user.phone_number}")
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = TelegramBot.objects.get(organization=org)
            logger.info(f"[TG_API] Bot found: @{bot.bot_username}, active={bot.is_active}")
            serializer = TelegramBotSerializer(bot)
            return Response(serializer.data)
        except TelegramBot.DoesNotExist:
            logger.info(f"[TG_API] No bot configured for org {organization_id}")
            return Response(
                {"error": "Telegram bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, organization_id):
        """Create or update Telegram bot configuration."""
        logger.info(f"[TG_API] POST create/update bot for org_id={organization_id}, user={request.user.phone_number}")
        logger.debug(f"[TG_API] Request data: {request.data}")

        org = self.get_organization(request, organization_id)
        if not org:
            logger.error(f"[TG_API] ERROR: Organization not found or access denied for org_id={organization_id}")
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if assistant exists
        if not hasattr(org, "assistant"):
            logger.error(f"[TG_API] ERROR: No AI assistant for org '{org.title}' (id={org.id})")
            return Response(
                {"error": "Organization must have an AI assistant configured first"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.info(f"[TG_API] Assistant found: '{org.assistant.name}', enabled={org.assistant.is_enabled}")

        serializer = TelegramBotCreateSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"[TG_API] ERROR: Invalid data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bot_token = serializer.validated_data["bot_token"]
        logger.info(f"[TG_API] Bot token validated: {bot_token[:20]}...")

        # Create or update bot
        bot, created = TelegramBot.objects.update_or_create(
            organization=org,
            defaults={
                "bot_token": bot_token,
                "is_active": serializer.validated_data.get("is_active", True),
            },
        )
        logger.info(f"[TG_API] Bot {'created' if created else 'updated'}: id={bot.id}")

        # Add bot link to organization contacts (before webhook setup, so link is added even if webhook fails)
        from messenger_bots.utils import add_bot_link_to_contacts
        add_bot_link_to_contacts(org, bot.bot_username)

        # Setup webhook
        base_url = request.build_absolute_uri("/").rstrip("/")
        logger.info(f"[TG_API] Setting up webhook with base_url={base_url}")
        success = TelegramBotService.setup_bot(bot, base_url)

        if not success:
            logger.error(f"[TG_API] ERROR: Failed to setup bot. Error: {bot.last_error}")
            return Response(
                {"error": "Failed to setup bot", "details": bot.last_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"[TG_API] SUCCESS: Bot @{bot.bot_username} configured, webhook_url={bot.webhook_url}")

        return Response(
            TelegramBotSerializer(bot).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, organization_id):
        """Delete Telegram bot configuration."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = TelegramBot.objects.get(organization=org)
            # Remove webhook first
            TelegramBotService(bot).delete_webhook()
            bot.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TelegramBot.DoesNotExist:
            return Response(
                {"error": "Telegram bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, organization_id):
        """Partial update of Telegram bot settings (is_active, is_ai_enabled)."""
        logger.info(f"[TG_API] PATCH for org_id={organization_id}, data={request.data}")

        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = TelegramBot.objects.get(organization=org)
        except TelegramBot.DoesNotExist:
            return Response(
                {"error": "Telegram bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        update_fields = []

        # Handle is_ai_enabled
        if "is_ai_enabled" in request.data:
            bot.is_ai_enabled = bool(request.data["is_ai_enabled"])
            update_fields.append("is_ai_enabled")
            logger.info(f"[TG_API] AI {'enabled' if bot.is_ai_enabled else 'disabled'} for org {organization_id}")

        # Handle is_active
        if "is_active" in request.data:
            bot.is_active = bool(request.data["is_active"])
            update_fields.append("is_active")
            logger.info(f"[TG_API] Bot {'activated' if bot.is_active else 'deactivated'} for org {organization_id}")

        if not update_fields:
            return Response(
                {"error": "No valid fields provided. Supported: is_ai_enabled, is_active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bot.save(update_fields=update_fields)

        return Response(TelegramBotSerializer(bot).data)


class TelegramBotSettingsAPIView(APIView):
    """API for updating Telegram bot settings (name, description, photo) via Telegram API."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def _get_bot(self, request, organization_id):
        """Get organization and bot, or return error response."""
        org = self.get_organization(request, organization_id)
        if not org:
            return None, None, Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            bot = TelegramBot.objects.get(organization=org)
            return org, bot, None
        except TelegramBot.DoesNotExist:
            return org, None, Response(
                {"error": "Telegram bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, organization_id):
        """Update bot settings: name, description, and/or photo (multipart/form-data)."""
        logger.info(f"[TG_SETTINGS] POST settings for org_id={organization_id}")

        org, bot, error_response = self._get_bot(request, organization_id)
        if error_response:
            return error_response

        service = TelegramBotService(bot)
        results = {}
        has_any_field = False

        # Handle name and description from request data
        name = request.data.get("name")
        description = request.data.get("description")

        if name is not None:
            has_any_field = True
            if len(name) > 64:
                results["name"] = {"success": False, "error": "Name must be 64 characters or less"}
            else:
                result = service.set_my_name(name)
                results["name"] = {
                    "success": result.get("ok", False),
                    **({"error": result.get("description")} if not result.get("ok") else {}),
                }

        if description is not None:
            has_any_field = True
            if len(description) > 512:
                results["description"] = {"success": False, "error": "Description must be 512 characters or less"}
            else:
                result = service.set_my_description(description)
                results["description"] = {
                    "success": result.get("ok", False),
                    **({"error": result.get("description")} if not result.get("ok") else {}),
                }

        # Handle photo file upload
        photo = request.FILES.get("photo")
        if photo:
            has_any_field = True
            # Validate file type
            content_type = photo.content_type
            if content_type not in ("image/jpeg", "image/png"):
                results["photo"] = {"success": False, "error": "Photo must be JPEG or PNG"}
            elif photo.size > 5 * 1024 * 1024:  # 5MB
                results["photo"] = {"success": False, "error": "Photo must be 5MB or less"}
            else:
                result = service.set_my_photo(photo)
                results["photo"] = {
                    "success": result.get("ok", False),
                    **({"error": result.get("description")} if not result.get("ok") else {}),
                }

        if not has_any_field:
            return Response(
                {"error": "No settings provided. Send name, description, and/or photo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"[TG_SETTINGS] Results: {results}")

        # Determine overall status
        all_success = all(r.get("success") for r in results.values())
        return Response(results, status=status.HTTP_200_OK if all_success else status.HTTP_207_MULTI_STATUS)

    def delete(self, request, organization_id):
        """Delete bot profile photo."""
        logger.info(f"[TG_SETTINGS] DELETE photo for org_id={organization_id}")

        org, bot, error_response = self._get_bot(request, organization_id)
        if error_response:
            return error_response

        service = TelegramBotService(bot)
        result = service.delete_my_photo()

        if result.get("ok"):
            return Response({"success": True})
        return Response(
            {"success": False, "error": result.get("description", "Unknown error")},
            status=status.HTTP_502_BAD_GATEWAY,
        )


class WhatsAppBotAPIView(APIView):
    """API for managing WhatsApp bot configuration."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def get(self, request, organization_id):
        """Get WhatsApp bot configuration."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(organization=org)
            serializer = WhatsAppBotSerializer(bot)
            return Response(serializer.data)
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, organization_id):
        """Create or update WhatsApp bot configuration."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(org, "assistant"):
            return Response(
                {"error": "Organization must have an AI assistant configured first"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WhatsAppBotCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create or update bot
        bot, created = WhatsAppBot.objects.update_or_create(
            organization=org,
            defaults={
                "phone_number_id": serializer.validated_data["phone_number_id"],
                "business_account_id": serializer.validated_data["business_account_id"],
                "access_token": serializer.validated_data["access_token"],
                "webhook_secret": serializer.validated_data.get("webhook_secret"),
                "is_active": serializer.validated_data.get("is_active", True),
            },
        )

        # Verify bot configuration
        if not WhatsAppBotService.verify_bot(bot):
            return Response(
                {"error": "Failed to verify bot", "details": bot.last_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return webhook URL for setup
        webhook_url = request.build_absolute_uri(
            f"/api/v1/messenger-bots/whatsapp/webhook/{organization_id}/"
        )

        response_data = WhatsAppBotSerializer(bot).data
        response_data["webhook_url"] = webhook_url

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, organization_id):
        """Delete WhatsApp bot configuration."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(organization=org)
            bot.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )


class BotChatsAPIView(APIView):
    """API for viewing bot chats."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id):
        """Get all bot chats for organization."""
        from django.db.models import Count, Q, Subquery, OuterRef

        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership:
                    return Response(
                        {"error": "Access denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        platform = request.query_params.get("platform")

        # Subquery for last message text
        last_message_subquery = BotMessage.objects.filter(
            chat=OuterRef("pk")
        ).order_by("-created_at").values("text")[:1]

        # Optimized queryset with annotations to avoid N+1 queries
        chats = BotChat.objects.filter(organization=org).annotate(
            _messages_count=Count("messages"),
            _unread_count=Count(
                "messages",
                filter=Q(messages__sender="user", messages__is_read=False)
            ),
            _last_message_text=Subquery(last_message_subquery),
        ).order_by("-last_message_at")

        if platform:
            chats = chats.filter(platform=platform)

        serializer = BotChatSerializer(chats, many=True)
        return Response(serializer.data)


class BotChatMessagesAPIView(APIView):
    """API for viewing messages in a bot chat."""

    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        """Get messages for a specific chat."""
        try:
            chat = BotChat.objects.select_related("organization").get(id=chat_id)
            org = chat.organization

            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership:
                    return Response(
                        {"error": "Access denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except BotChat.DoesNotExist:
            return Response(
                {"error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mark all user messages as read when admin opens the chat
        chat.messages.filter(sender="user", is_read=False).update(is_read=True)

        messages = chat.messages.all().order_by("created_at")
        serializer = BotMessageSerializer(messages, many=True)
        return Response(serializer.data)


class BotStatusAPIView(APIView):
    """API for checking bot status."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id):
        """Get status of all bots for organization."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership:
                    return Response(
                        {"error": "Access denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = {
            "has_assistant": hasattr(org, "assistant") and org.assistant.is_enabled,
            "telegram": None,
            "whatsapp": None,
        }

        try:
            tg_bot = TelegramBot.objects.get(organization=org)
            result["telegram"] = {
                "configured": True,
                "active": tg_bot.is_active,
                "username": tg_bot.bot_username,
                "last_error": tg_bot.last_error,
            }
        except TelegramBot.DoesNotExist:
            result["telegram"] = {"configured": False}

        try:
            wa_bot = WhatsAppBot.objects.get(organization=org)
            result["whatsapp"] = {
                "configured": True,
                "active": wa_bot.is_active,
                "provider": wa_bot.provider,
                "provider_display": wa_bot.get_provider_display(),
                "is_connected": wa_bot.is_connected,
                "last_error": wa_bot.last_error,
            }
            # Add provider-specific info
            if wa_bot.provider == WhatsAppProvider.WAHA:
                result["whatsapp"].update({
                    "session_status": wa_bot.session_status,
                    "session_status_display": wa_bot.get_session_status_display(),
                    "connected_phone": wa_bot.connected_phone_number,
                })
            else:
                result["whatsapp"]["phone_number"] = wa_bot.display_phone_number
        except WhatsAppBot.DoesNotExist:
            result["whatsapp"] = {"configured": False}

        return Response(result)


class BotUnreadCountAPIView(APIView):
    """
    API for getting total unread message count across all bot chats.
    Used for displaying badge/notification in the menu.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id):
        """Get total unread count for all bot chats."""
        from django.db.models import Count, Q

        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership:
                    return Response(
                        {"error": "Access denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get unread counts per platform
        telegram_unread = BotMessage.objects.filter(
            chat__organization=org,
            chat__platform=BotPlatform.TELEGRAM,
            sender=BotMessage.USER,
            is_read=False,
        ).count()

        whatsapp_unread = BotMessage.objects.filter(
            chat__organization=org,
            chat__platform=BotPlatform.WHATSAPP,
            sender=BotMessage.USER,
            is_read=False,
        ).count()

        # Get unread from website chats (ChatMessage model)
        from organizations.models import ChatMessage, Chat

        website_unread = 0
        if hasattr(org, 'assistant'):
            website_unread = ChatMessage.objects.filter(
                chat__assistant=org.assistant,
                sender=ChatMessage.USER,
                is_read=False,
            ).count()

        total = telegram_unread + whatsapp_unread + website_unread

        return Response({
            "total": total,
            "telegram": telegram_unread,
            "whatsapp": whatsapp_unread,
            "website": website_unread,
        })


class AutoCreateTelegramBotAPIView(APIView):
    """
    API for one-click Telegram bot creation.
    Automatically creates a bot via BotFather using userbot.
    """

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        logger.debug(f"[AUTO_CREATE] get_organization: org_id={organization_id}, user_id={request.user.id}")
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    logger.warning(f"[AUTO_CREATE] Access denied for user {request.user.id} to org {organization_id}")
                    return None
            return org
        except Organization.DoesNotExist:
            logger.warning(f"[AUTO_CREATE] Organization not found: id={organization_id}")
            return None

    def get(self, request, organization_id):
        """Get status of bot creation request."""
        logger.info(f"[AUTO_CREATE] GET status for org_id={organization_id}")
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get latest creation request
        request_obj = BotCreationRequest.objects.filter(
            organization=org
        ).order_by("-created_at").first()

        if not request_obj:
            logger.info(f"[AUTO_CREATE] No creation request found for org {organization_id}")
            return Response(
                {"error": "No bot creation request found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info(f"[AUTO_CREATE] Found request id={request_obj.id}, status={request_obj.status}")
        serializer = BotCreationRequestSerializer(request_obj)
        return Response(serializer.data)

    def post(self, request, organization_id):
        """
        Create a new Telegram bot automatically.
        Bot name format: "{OrgTitle} APZ"
        """
        logger.info(f"[AUTO_CREATE] ====== START AUTO-CREATE BOT ======")
        logger.info(f"[AUTO_CREATE] org_id={organization_id}, user={request.user.phone_number} (id={request.user.id})")

        org = self.get_organization(request, organization_id)
        if not org:
            logger.error(f"[AUTO_CREATE] ERROR: Organization not found or access denied")
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )
        logger.info(f"[AUTO_CREATE] Organization: '{org.title}' (id={org.id})")

        # Check if assistant exists
        if not hasattr(org, "assistant"):
            logger.error(f"[AUTO_CREATE] ERROR: No AI assistant configured for org '{org.title}'")
            return Response(
                {"error": "Organization must have an AI assistant configured first"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.info(f"[AUTO_CREATE] Assistant: '{org.assistant.name}', enabled={org.assistant.is_enabled}")

        # Check if bot already exists
        existing_bot = TelegramBot.objects.filter(organization=org).first()
        if existing_bot:
            logger.error(f"[AUTO_CREATE] ERROR: Bot already exists: @{existing_bot.bot_username}")
            return Response(
                {"error": "Telegram bot already exists for this organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if there's a pending request
        pending_request = BotCreationRequest.objects.filter(
            organization=org,
            status__in=[BotCreationStatus.PENDING, BotCreationStatus.IN_PROGRESS],
        ).first()

        if pending_request:
            logger.warning(f"[AUTO_CREATE] Pending request exists: id={pending_request.id}, status={pending_request.status}")
            return Response(
                {
                    "error": "Bot creation already in progress",
                    "request_id": pending_request.id,
                    "status": pending_request.status,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Check if userbots are available
        available_userbots = TelegramUserbot.objects.filter(
            is_active=True,
            is_authenticated=True,
            bots_created_today__lt=20,
        )
        userbots_count = available_userbots.count()
        logger.info(f"[AUTO_CREATE] Available userbots: {userbots_count}")

        if userbots_count == 0:
            # Log details about why no userbots available
            all_userbots = TelegramUserbot.objects.all()
            for ub in all_userbots:
                logger.warning(f"[AUTO_CREATE] Userbot {ub.phone_number}: active={ub.is_active}, auth={ub.is_authenticated}, today={ub.bots_created_today}/20")
            logger.error(f"[AUTO_CREATE] ERROR: No available userbots")
            return Response(
                {"error": "Bot creation service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Log available userbots
        for ub in available_userbots:
            logger.info(f"[AUTO_CREATE] Available userbot: {ub.phone_number}, today={ub.bots_created_today}/20")

        # Generate bot name
        bot_name = f"{org.title} APZ"
        if len(bot_name) > 64:
            bot_name = f"{org.title[:57]} APZ"
        logger.info(f"[AUTO_CREATE] Bot name: '{bot_name}'")

        # Create request with base_url for webhook
        base_url = request.build_absolute_uri("/").rstrip("/")
        creation_request = BotCreationRequest.objects.create(
            organization=org,
            requested_by=request.user,
            bot_name=bot_name,
            status=BotCreationStatus.PENDING,
            base_url=base_url,
        )
        logger.info(f"[AUTO_CREATE] Created BotCreationRequest id={creation_request.id}, base_url={base_url}")

        # Start async task
        from messenger_bots.tasks import create_telegram_bot_task

        logger.info(f"[AUTO_CREATE] Starting Celery task with base_url={base_url}")
        task = create_telegram_bot_task.delay(creation_request.id, base_url)
        logger.info(f"[AUTO_CREATE] Celery task started: task_id={task.id}")
        logger.info(f"[AUTO_CREATE] ====== END AUTO-CREATE BOT (accepted) ======")

        return Response(
            {
                "message": "Bot creation started",
                "request_id": creation_request.id,
                "bot_name": bot_name,
                "status": BotCreationStatus.PENDING,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class BotCreationStatusAPIView(APIView):
    """API for checking bot creation request status."""

    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):
        """Get status of a specific bot creation request."""
        try:
            creation_request = BotCreationRequest.objects.select_related(
                "organization"
            ).get(id=request_id)
        except BotCreationRequest.DoesNotExist:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify access
        org = creation_request.organization
        if org.owner != request.user:
            membership = org.memberships.filter(user=request.user).first()
            if not membership:
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = BotCreationRequestSerializer(creation_request)
        return Response(serializer.data)


# ============== WAHA WhatsApp API Views ==============

class WhatsAppWAHABotAPIView(APIView):
    """API for managing WhatsApp bot with WAHA provider."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def get(self, request, organization_id):
        """Get WhatsApp WAHA bot configuration and status."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(organization=org)
            serializer = WhatsAppBotSerializer(bot)
            return Response(serializer.data)
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, organization_id):
        """Create WhatsApp bot with WAHA provider."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if assistant exists
        if not hasattr(org, "assistant"):
            return Response(
                {"error": "Organization must have an AI assistant configured first"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if bot already exists
        if WhatsAppBot.objects.filter(organization=org).exists():
            return Response(
                {"error": "WhatsApp bot already exists for this organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WhatsAppBotWAHACreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create bot with WAHA provider
        bot = WhatsAppBot.objects.create(
            organization=org,
            provider=WhatsAppProvider.WAHA,
            is_active=serializer.validated_data.get("is_active", True),
        )

        # Start WAHA session
        try:
            service = WhatsAppServiceFactory.get_service(bot)
            service.start_session()
        except Exception as e:
            logger.error(f"Failed to start WAHA session for org {org.id}: {e}")
            bot.last_error = str(e)
            bot.save(update_fields=["last_error"])

        return Response(
            WhatsAppBotSerializer(bot).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, organization_id):
        """Delete WhatsApp WAHA bot configuration."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(organization=org)

            # Stop WAHA session if it's WAHA provider
            if bot.provider == WhatsAppProvider.WAHA:
                try:
                    service = WhatsAppServiceFactory.get_service(bot)
                    service.stop_session()
                except Exception as e:
                    logger.warning(f"Failed to stop WAHA session for org {org.id}: {e}")

            bot.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, organization_id):
        """Partial update of WhatsApp bot settings (is_active, is_ai_enabled)."""
        logger.info(f"[WAHA_API] PATCH for org_id={organization_id}, data={request.data}")

        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(organization=org)
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        update_fields = []

        # Handle is_ai_enabled
        if "is_ai_enabled" in request.data:
            bot.is_ai_enabled = bool(request.data["is_ai_enabled"])
            update_fields.append("is_ai_enabled")
            logger.info(f"[WAHA_API] AI {'enabled' if bot.is_ai_enabled else 'disabled'} for org {organization_id}")

        # Handle is_active
        if "is_active" in request.data:
            bot.is_active = bool(request.data["is_active"])
            update_fields.append("is_active")
            logger.info(f"[WAHA_API] Bot {'activated' if bot.is_active else 'deactivated'} for org {organization_id}")

        if not update_fields:
            return Response(
                {"error": "No valid fields provided. Supported: is_ai_enabled, is_active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bot.save(update_fields=update_fields)

        return Response(WhatsAppBotSerializer(bot).data)


class WhatsAppWAHASessionAPIView(APIView):
    """API for managing WAHA session (start, stop, get QR code)."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def get(self, request, organization_id):
        """Get current session status and QR code if available."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get live status from WAHA
        service = WhatsAppServiceFactory.get_service(bot)
        connection_status = service.check_connection()

        # Get QR code if needed
        qr_code = None
        if bot.session_status in [WhatsAppSessionStatus.PENDING, WhatsAppSessionStatus.SCAN_QR]:
            qr_code = service.get_qr_code()

        return Response({
            "session_name": bot.waha_session_name,
            "status": bot.session_status,
            "status_display": bot.get_session_status_display(),
            "qr_code": qr_code,
            "connected_phone": bot.connected_phone_number,
            "is_healthy": service.is_healthy(),
            "waha_status": connection_status,
        })

    def post(self, request, organization_id):
        """Start or restart WAHA session."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = WhatsAppServiceFactory.get_service(bot)

        # Start session
        try:
            success = service.start_session()
            if success:
                bot.session_status = WhatsAppSessionStatus.PENDING
                bot.last_error = None
                bot.save(update_fields=["session_status", "last_error"])
                return Response({"message": "Session started", "status": bot.session_status})
            else:
                return Response(
                    {"error": "Failed to start session"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            bot.last_error = str(e)
            bot.save(update_fields=["last_error"])
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, organization_id):
        """Stop WAHA session (logout)."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = WhatsAppServiceFactory.get_service(bot)

        try:
            success = service.stop_session()
            bot.session_status = WhatsAppSessionStatus.DISCONNECTED
            bot.connected_phone_number = None
            bot.save(update_fields=["session_status", "connected_phone_number"])
            return Response({"message": "Session stopped", "status": bot.session_status})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WhatsAppWAHAQRCodeAPIView(APIView):
    """API for getting WAHA QR code for authentication."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def get(self, request, organization_id):
        """Get QR code for WhatsApp authentication."""
        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if already authenticated
        if bot.session_status == WhatsAppSessionStatus.AUTHENTICATED:
            return Response({
                "qr_code": None,
                "message": "Already authenticated",
                "connected_phone": bot.connected_phone_number,
            })

        service = WhatsAppServiceFactory.get_service(bot)
        qr_code = service.get_qr_code()

        if qr_code:
            # Update status to indicate QR is ready
            if bot.session_status == WhatsAppSessionStatus.PENDING:
                bot.session_status = WhatsAppSessionStatus.SCAN_QR
                bot.save(update_fields=["session_status"])

            return Response({
                "qr_code": qr_code,
                "message": "Scan this QR code with WhatsApp",
            })
        else:
            return Response({
                "qr_code": None,
                "message": "QR code not available. Try starting the session first.",
                "session_status": bot.session_status,
            })


class WhatsAppRebindAPIView(APIView):
    """API for rebinding WhatsApp phone number (stop old session, start new, get QR)."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def post(self, request, organization_id):
        """Rebind WhatsApp phone number: stop old session, save previous phone, start new session."""
        logger.info(f"[WA_REBIND] POST rebind for org_id={organization_id}")

        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if there's a phone to rebind
        if not bot.connected_phone_number:
            return Response(
                {"error": "No phone number connected to rebind"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = WhatsAppServiceFactory.get_service(bot)

        # 1. Save previous phone info
        bot.previous_phone_number = bot.connected_phone_number
        bot.phone_changed_at = timezone.now()

        # 2. Logout and delete current session completely
        try:
            # First logout (disconnects WhatsApp account)
            service.logout_session()
            logger.info(f"[WA_REBIND] Session logged out for org {organization_id}")
        except Exception as e:
            logger.warning(f"[WA_REBIND] Logout failed (continuing): {e}")

        try:
            # Then delete session data from WAHA
            service.delete_session()
            logger.info(f"[WA_REBIND] Session deleted for org {organization_id}")
        except Exception as e:
            logger.warning(f"[WA_REBIND] Delete failed (continuing): {e}")

        # 3. Clear current phone and update status
        bot.connected_phone_number = None
        bot.session_status = WhatsAppSessionStatus.SCAN_QR
        bot.save(update_fields=[
            "previous_phone_number",
            "phone_changed_at",
            "connected_phone_number",
            "session_status",
        ])

        # 4. Start new session
        try:
            service.start_session()
            logger.info(f"[WA_REBIND] New session started for org {organization_id}")
        except Exception as e:
            logger.error(f"[WA_REBIND] Failed to start new session: {e}")
            bot.last_error = str(e)
            bot.session_status = WhatsAppSessionStatus.FAILED
            bot.save(update_fields=["last_error", "session_status"])
            return Response(
                {"error": f"Failed to start new session: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 5. Get QR code for new phone
        qr_code = service.get_qr_code()

        logger.info(f"[WA_REBIND] Rebind successful: prev_phone={bot.previous_phone_number}, qr={'yes' if qr_code else 'no'}")

        return Response({
            "success": True,
            "previous_phone_number": bot.previous_phone_number,
            "phone_changed_at": bot.phone_changed_at.isoformat(),
            "session_status": bot.session_status,
            "qr_code": qr_code,
        })


class WhatsAppSessionLogoutAPIView(APIView):
    """API for logging out WhatsApp session (requires QR re-scan)."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def post(self, request, organization_id):
        """Logout from WhatsApp (requires QR re-scan to reconnect)."""
        logger.info(f"[WA_LOGOUT] POST logout for org_id={organization_id}")

        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = WhatsAppServiceFactory.get_service(bot)

        try:
            success = service.logout_session()
            if success:
                bot.session_status = WhatsAppSessionStatus.DISCONNECTED
                bot.connected_phone_number = None
                bot.save(update_fields=["session_status", "connected_phone_number"])
                logger.info(f"[WA_LOGOUT] Session logged out for org {organization_id}")
                return Response({
                    "success": True,
                    "message": "Logged out from WhatsApp. QR scan required to reconnect.",
                })
            else:
                return Response(
                    {"error": "Failed to logout"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            logger.error(f"[WA_LOGOUT] Logout failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WhatsAppSessionDeleteAPIView(APIView):
    """API for deleting WhatsApp session completely."""

    permission_classes = [IsAuthenticated]

    def get_organization(self, request, organization_id):
        """Get organization and verify ownership."""
        try:
            org = Organization.objects.get(id=organization_id)
            if org.owner != request.user:
                membership = org.memberships.filter(user=request.user).first()
                if not membership or not membership.role.can_edit_organization:
                    return None
            return org
        except Organization.DoesNotExist:
            return None

    def post(self, request, organization_id):
        """Delete session completely (removes all session data from WAHA)."""
        logger.info(f"[WA_DELETE] POST delete session for org_id={organization_id}")

        org = self.get_organization(request, organization_id)
        if not org:
            return Response(
                {"error": "Organization not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bot = WhatsAppBot.objects.get(
                organization=org,
                provider=WhatsAppProvider.WAHA,
            )
        except WhatsAppBot.DoesNotExist:
            return Response(
                {"error": "WhatsApp WAHA bot not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = WhatsAppServiceFactory.get_service(bot)

        try:
            success = service.delete_session()
            if success:
                bot.session_status = WhatsAppSessionStatus.DISCONNECTED
                bot.connected_phone_number = None
                bot.save(update_fields=["session_status", "connected_phone_number"])
                logger.info(f"[WA_DELETE] Session deleted for org {organization_id}")
                return Response({
                    "success": True,
                    "message": "Session deleted completely.",
                })
            else:
                return Response(
                    {"error": "Failed to delete session"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            logger.error(f"[WA_DELETE] Delete failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
