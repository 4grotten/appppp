import hashlib
import hmac
import logging
import requests
from typing import Optional
from django.utils import timezone

from messenger_bots.models import WhatsAppBot, BotChat, BotMessage, BotPlatform

logger = logging.getLogger(__name__)


class WhatsAppBotService:
    """Service for interacting with WhatsApp Cloud API."""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, whatsapp_bot: WhatsAppBot):
        self.bot = whatsapp_bot

    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make a request to WhatsApp Cloud API."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.bot.access_token}",
            "Content-Type": "application/json",
        }
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)

            result = response.json()

            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                logger.error(f"WhatsApp API error: {error_msg}")
                self.bot.last_error = error_msg
                self.bot.save(update_fields=["last_error"])
                return {"ok": False, "error": result["error"]}

            return {"ok": True, "result": result}
        except requests.RequestException as e:
            logger.error(f"WhatsApp request failed: {e}")
            self.bot.last_error = str(e)
            self.bot.save(update_fields=["last_error"])
            return {"ok": False, "error": {"message": str(e)}}

    def get_phone_number_info(self) -> Optional[dict]:
        """Get phone number information."""
        result = self._make_request("GET", self.bot.phone_number_id)
        if result.get("ok"):
            info = result.get("result", {})
            self.bot.display_phone_number = info.get("display_phone_number")
            self.bot.last_error = None
            self.bot.save(update_fields=["display_phone_number", "last_error"])
            return info
        return None

    def send_message(self, to: str, text: str) -> Optional[dict]:
        """Send a text message."""
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        endpoint = f"{self.bot.phone_number_id}/messages"
        result = self._make_request("POST", endpoint, data)
        if result.get("ok"):
            return result.get("result")
        return None

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        endpoint = f"{self.bot.phone_number_id}/messages"
        result = self._make_request("POST", endpoint, data)
        return result.get("ok", False)

    @classmethod
    def verify_webhook_signature(cls, whatsapp_bot: WhatsAppBot, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Meta."""
        if not whatsapp_bot.webhook_secret:
            return True  # Skip verification if no secret configured

        expected_signature = hmac.new(
            whatsapp_bot.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    @classmethod
    def process_webhook_update(cls, whatsapp_bot: WhatsAppBot, data: dict) -> Optional[str]:
        """
        Process incoming webhook update from WhatsApp.
        Returns the response text to send back.
        """
        entry = data.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]
        message_type = message.get("type")

        # Only handle text messages for now
        if message_type != "text":
            return None

        from_number = message.get("from")
        text = message.get("text", {}).get("body", "")
        message_id = message.get("id")

        if not text or not from_number:
            return None

        # Get contact info
        contacts = value.get("contacts", [])
        user_name = ""
        if contacts:
            profile = contacts[0].get("profile", {})
            user_name = profile.get("name", "")

        # Get or create chat
        chat, created = BotChat.objects.get_or_create(
            organization=whatsapp_bot.organization,
            platform=BotPlatform.WHATSAPP,
            platform_chat_id=from_number,
            defaults={
                "platform_user_id": from_number,
                "user_name": user_name,
                "user_phone": from_number,
            }
        )

        if not created and user_name and chat.user_name != user_name:
            chat.user_name = user_name
            chat.save(update_fields=["user_name"])

        # Save incoming message
        BotMessage.objects.create(
            chat=chat,
            sender=BotMessage.USER,
            text=text,
            platform_message_id=message_id,
        )

        # Update last message time
        chat.last_message_at = timezone.now()
        chat.save(update_fields=["last_message_at"])

        # Mark as read
        service = cls(whatsapp_bot)
        service.mark_as_read(message_id)

        # Get AI response
        from messenger_bots.services.assistant import BotAssistantService
        response_text = BotAssistantService.get_response(
            organization=whatsapp_bot.organization,
            question=text,
        )

        # Send response
        result = service.send_message(from_number, response_text)

        # Save assistant response
        if result:
            wa_messages = result.get("messages", [])
            response_message_id = wa_messages[0].get("id") if wa_messages else None
            BotMessage.objects.create(
                chat=chat,
                sender=BotMessage.ASSISTANT,
                text=response_text,
                platform_message_id=response_message_id,
            )

        return response_text

    @classmethod
    def verify_bot(cls, whatsapp_bot: WhatsAppBot) -> bool:
        """Verify bot configuration by getting phone number info."""
        service = cls(whatsapp_bot)
        info = service.get_phone_number_info()
        return info is not None
