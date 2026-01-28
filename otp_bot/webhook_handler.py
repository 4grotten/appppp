"""Webhook handler for OTP Bot incoming messages.

Handles text and voice messages for the Finance AI Voice Assistant.
Voice flow: Download -> STT (ElevenLabs) -> AI -> TTS (ElevenLabs) -> Send Voice

Thread-safe singletons using functools.lru_cache.
Text message AI processing is offloaded to Celery for fast webhook response.
"""

import logging
from functools import lru_cache

from .models import ChatSession, UserVoicePreference
from .services.waha_otp import WAHAOTPClient
from .services.ai_service import FinanceAIService
from .services.elevenlabs import ElevenLabsService

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_waha_client() -> WAHAOTPClient:
    """Get singleton WAHA client instance (thread-safe via lru_cache)."""
    logger.info("[WEBHOOK_HANDLER] Initializing WAHA client singleton")
    return WAHAOTPClient()


@lru_cache(maxsize=1)
def get_ai_service() -> FinanceAIService:
    """Get singleton AI service instance (thread-safe via lru_cache)."""
    logger.info("[WEBHOOK_HANDLER] Initializing AI service singleton")
    return FinanceAIService()


@lru_cache(maxsize=1)
def get_elevenlabs_service() -> ElevenLabsService:
    """Get singleton ElevenLabs service instance (thread-safe via lru_cache)."""
    logger.info("[WEBHOOK_HANDLER] Initializing ElevenLabs service singleton")
    return ElevenLabsService()


class OTPBotWebhookHandler:
    """Handle incoming WhatsApp messages for OTP Bot.

    Routes messages to appropriate handlers based on type:
    - Text messages -> AI response (text or voice based on preference)
    - Voice messages -> STT -> AI -> TTS -> Voice response
    - Commands (/voice, /clear) -> Special handling
    """

    def __init__(self):
        # Use singleton services to avoid repeated instantiation
        self.waha = get_waha_client()
        self.ai = get_ai_service()
        self.elevenlabs = get_elevenlabs_service()

    def handle(self, data: dict) -> None:
        """Route incoming message to appropriate handler.

        Args:
            data: Webhook payload from WAHA
        """
        event = data.get("event")

        if event != "message":
            logger.debug(f"[WEBHOOK_HANDLER] Ignoring event: {event}")
            return

        payload = data.get("payload", {})

        # Skip our own messages
        if payload.get("fromMe"):
            return

        # Skip group messages
        from_field = payload.get("from", "")
        if "@g.us" in from_field:
            logger.debug("[WEBHOOK_HANDLER] Ignoring group message")
            return

        # Extract phone - handle both @c.us and @s.whatsapp.net formats
        if "@" in from_field:
            phone = from_field.split("@")[0]
        else:
            phone = from_field

        # Body can be None for voice messages
        body = payload.get("body")
        text = body.strip() if body else ""
        has_media = payload.get("hasMedia", False)

        # Get message ID - WAHA uses format: {fromMe}_{chatId}_{id}
        # We need to construct this from payload data
        msg_id_raw = payload.get("id", "")
        if isinstance(msg_id_raw, dict):
            msg_id = msg_id_raw.get("id", "")
        else:
            msg_id = str(msg_id_raw)

        # Construct full message ID for WAHA API: false_{chatId}_{messageId}
        from_me = "true" if payload.get("fromMe", False) else "false"
        chat_id = from_field  # e.g., "996552154092@s.whatsapp.net"
        message_id = f"{from_me}_{chat_id}_{msg_id}"

        # Also try to get media URL directly from payload (WAHA provides this when ready)
        media_url = None
        _data = payload.get("_data", {})
        message_content = _data.get("message", {})
        audio_msg = message_content.get("audioMessage", {})
        if audio_msg:
            media_url = audio_msg.get("url")

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Message from {masked_phone}: {text[:50] if text else '(media)'}")

        try:
            # Check for commands
            if text.lower() == "/voice":
                self._handle_voice_command(phone)
                return

            if text.lower() == "/clear":
                self._handle_clear_command(phone)
                return

            # Check if voice message
            if has_media and self._is_voice_message(payload):
                logger.info(f"[WEBHOOK_HANDLER] Voice message detected, message_id={message_id[:50]}...")
                self._handle_voice_message(phone, message_id, payload)
                return

            # Handle text message
            if text:
                self._handle_text_message(phone, text)

        except Exception as e:
            logger.error(f"[WEBHOOK_HANDLER] Error handling message: {e}", exc_info=True)
            self._send_text(phone, "Произошла ошибка. Попробуйте ещё раз.")

    def _handle_text_message(self, phone: str, text: str) -> None:
        """Queue text message for async AI processing via Celery.

        AI calls can take 1-5 seconds which would block the webhook response.
        Offloading to Celery ensures fast webhook acknowledgment.

        Args:
            phone: User's phone number
            text: Message text
        """
        from .tasks import process_otp_text_message_task

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Text message from {masked_phone}, queuing task")

        # Check voice preference
        pref = UserVoicePreference.get_preference(phone)

        # Queue the text processing task
        process_otp_text_message_task.delay(
            phone=phone,
            text=text,
            voice_mode=pref.voice_enabled,
        )

        logger.info(f"[WEBHOOK_HANDLER] Text task queued for {masked_phone}")

    def _handle_voice_message(self, phone: str, message_id: str, payload: dict) -> None:
        """Queue voice message for async processing via Celery.

        Voice processing (download, STT, AI, TTS, send) is offloaded to a
        Celery task to avoid blocking the webhook handler.

        Args:
            phone: User's phone number
            message_id: WhatsApp message ID for downloading media
            payload: Full message payload from webhook
        """
        from .tasks import process_otp_voice_message_task

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Voice message from {masked_phone}, queuing task")

        # Queue the voice processing task
        process_otp_voice_message_task.delay(
            phone=phone,
            message_id=message_id,
            payload=payload,
        )

        logger.info(f"[WEBHOOK_HANDLER] Voice task queued for {masked_phone}")

    def _handle_voice_command(self, phone: str) -> None:
        """Handle /voice command - toggle voice mode.

        Args:
            phone: User's phone number
        """
        pref = UserVoicePreference.get_preference(phone)
        new_state = pref.toggle()

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Voice mode toggled for {masked_phone}: {new_state}")

        if new_state:
            message = (
                "Голосовой режим ВКЛЮЧЁН\n\n"
                "Теперь я буду отвечать голосом на все сообщения.\n"
                "Отправьте /voice ещё раз чтобы выключить."
            )
        else:
            message = (
                "Голосовой режим ВЫКЛЮЧЕН\n\n"
                "Теперь я буду отвечать текстом на текст, голосом на голос.\n"
                "Отправьте /voice чтобы включить."
            )

        self._send_text(phone, message)

    def _handle_clear_command(self, phone: str) -> None:
        """Handle /clear command - clear chat history.

        Args:
            phone: User's phone number
        """
        session = ChatSession.get_or_create_session(phone)
        session.clear()

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Chat history cleared for {masked_phone}")

        self._send_text(phone, "История чата очищена. Начнём сначала!")

    def _is_voice_message(self, payload: dict) -> bool:
        """Check if message is a voice message.

        Args:
            payload: Message payload from WAHA

        Returns:
            True if voice/audio message (ptt = push-to-talk)
        """
        # Check mediaType field
        media_type = payload.get("mediaType", "")
        if media_type in ("audio", "ptt"):
            return True

        # Check for audioMessage in message structure (WAHA noweb format)
        _data = payload.get("_data", {})
        message = _data.get("message", {})
        if message.get("audioMessage"):
            return True

        return False

    def _send_text(self, phone: str, text: str) -> bool:
        """Send text message via WAHA.

        Args:
            phone: Recipient phone number
            text: Message text

        Returns:
            True if sent successfully
        """
        return self.waha.send_text(f"+{phone}", text)

    def _send_voice_response(self, phone: str, text: str) -> None:
        """Convert text to voice and send via WAHA.

        Uses ElevenLabs TTS to convert text to speech, then sends
        as voice message. Falls back to text if TTS fails.

        Args:
            phone: Recipient phone number
            text: Text to convert to voice
        """
        masked_phone = self._mask_phone(phone)

        # Check if ElevenLabs is configured
        if not self.elevenlabs.is_configured():
            logger.warning(f"[WEBHOOK_HANDLER] ElevenLabs not configured, sending text to {masked_phone}")
            self._send_text(phone, text)
            return

        # Convert text to speech
        logger.info(f"[WEBHOOK_HANDLER] TTS for {masked_phone}: {len(text)} chars")
        audio_bytes = self.elevenlabs.text_to_speech(text)

        if not audio_bytes:
            logger.warning(f"[WEBHOOK_HANDLER] TTS failed for {masked_phone}, falling back to text")
            self._send_text(phone, text)
            return

        # Send voice message
        logger.info(f"[WEBHOOK_HANDLER] Sending voice to {masked_phone}: {len(audio_bytes)} bytes")
        success = self.waha.send_voice_base64(f"+{phone}", audio_bytes)

        if not success:
            logger.warning(f"[WEBHOOK_HANDLER] Voice send failed for {masked_phone}, falling back to text")
            self._send_text(phone, text)

    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for logging.

        Args:
            phone: Phone number

        Returns:
            Masked phone (e.g., +7900123***)
        """
        if len(phone) > 7:
            return f"+{phone[:7]}***"
        return f"+{phone}"
