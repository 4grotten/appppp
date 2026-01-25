"""Webhook handler for OTP Bot incoming messages.

Handles text and voice messages for the Finance AI Voice Assistant.
Voice flow: Download -> STT (ElevenLabs) -> AI -> TTS (ElevenLabs) -> Send Voice
"""

import logging
from typing import Optional

from .models import ChatSession, UserVoicePreference
from .services.waha_otp import WAHAOTPClient
from .services.ai_service import FinanceAIService
from .services.elevenlabs import ElevenLabsService

logger = logging.getLogger(__name__)


class OTPBotWebhookHandler:
    """Handle incoming WhatsApp messages for OTP Bot.

    Routes messages to appropriate handlers based on type:
    - Text messages -> AI response (text or voice based on preference)
    - Voice messages -> STT -> AI -> TTS -> Voice response
    - Commands (/voice, /clear) -> Special handling
    """

    def __init__(self):
        self.waha = WAHAOTPClient()
        self.ai = FinanceAIService()
        self.elevenlabs = ElevenLabsService()

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

        # Get message ID - can be dict or string
        msg_id = payload.get("id", "")
        if isinstance(msg_id, dict):
            message_id = msg_id.get("id", "")
        else:
            message_id = str(msg_id)

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
                self._handle_voice_message(phone, message_id)
                return

            # Handle text message
            if text:
                self._handle_text_message(phone, text)

        except Exception as e:
            logger.error(f"[WEBHOOK_HANDLER] Error handling message: {e}", exc_info=True)
            self._send_text(phone, "Произошла ошибка. Попробуйте ещё раз.")

    def _handle_text_message(self, phone: str, text: str) -> None:
        """Process text message and send AI response.

        Args:
            phone: User's phone number
            text: Message text
        """
        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Processing text from {masked_phone}")

        # Get or create chat session
        session = ChatSession.get_or_create_session(phone)

        # Add user message to history
        session.add_message("user", text)

        # Check voice preference
        pref = UserVoicePreference.get_preference(phone)
        voice_mode = pref.voice_enabled

        # Get AI response
        response = self.ai.get_response(
            phone_number=phone,
            question=text,
            chat_history=session.get_history()[:-1],  # Exclude current message
            voice_mode=voice_mode,
        )

        # Add assistant response to history
        session.add_message("assistant", response)

        # Send response based on preference
        if voice_mode:
            self._send_voice_response(phone, response)
        else:
            self._send_text(phone, response)

    def _handle_voice_message(self, phone: str, message_id: str) -> None:
        """Process voice message: Download -> STT -> AI -> TTS -> Voice response.

        Full voice pipeline:
        1. Download voice message from WAHA
        2. Transcribe using ElevenLabs STT
        3. Get AI response (voice_mode=True for shorter text)
        4. Convert to speech using ElevenLabs TTS
        5. Send voice message via WAHA

        Falls back to text on any error.

        Args:
            phone: User's phone number
            message_id: WhatsApp message ID for downloading media
        """
        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Voice message from {masked_phone}")

        # Check if ElevenLabs is configured
        if not self.elevenlabs.is_configured():
            logger.warning("[WEBHOOK_HANDLER] ElevenLabs not configured, falling back to text prompt")
            self._send_text(
                phone,
                "Голосовые сообщения временно недоступны. "
                "Пожалуйста, напишите текстом."
            )
            return

        # Step 1: Download voice message
        logger.info(f"[WEBHOOK_HANDLER] Downloading voice from {masked_phone}")
        audio_bytes = self.waha.download_media(message_id)

        if not audio_bytes:
            logger.error(f"[WEBHOOK_HANDLER] Failed to download voice from {masked_phone}")
            self._send_text(
                phone,
                "Не удалось загрузить голосовое сообщение. "
                "Попробуйте ещё раз или напишите текстом."
            )
            return

        # Step 2: Speech-to-Text
        logger.info(f"[WEBHOOK_HANDLER] Transcribing voice from {masked_phone}")
        transcribed_text = self.elevenlabs.speech_to_text(audio_bytes)

        if not transcribed_text:
            logger.warning(f"[WEBHOOK_HANDLER] STT failed for {masked_phone}")
            self._send_text(
                phone,
                "Не удалось распознать речь. "
                "Попробуйте говорить чётче или напишите текстом."
            )
            return

        logger.info(f"[WEBHOOK_HANDLER] Transcribed from {masked_phone}: {transcribed_text[:50]}...")

        # Step 3: Get or create chat session and add message
        session = ChatSession.get_or_create_session(phone)
        session.add_message("user", transcribed_text)

        # Step 4: Get AI response (voice_mode=True for shorter responses)
        response = self.ai.get_response(
            phone_number=phone,
            question=transcribed_text,
            chat_history=session.get_history()[:-1],
            voice_mode=True,  # Always use voice mode for voice input
        )

        session.add_message("assistant", response)

        # Step 5: Text-to-Speech and send
        self._send_voice_response(phone, response)

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
