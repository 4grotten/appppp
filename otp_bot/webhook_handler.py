"""Webhook handler for OTP Bot incoming messages.

Handles text and voice messages for the Finance AI Voice Assistant.
Voice flow: Download -> STT (ElevenLabs) -> AI -> TTS (ElevenLabs) -> Send Voice
"""

import base64
import logging
from typing import Optional

import requests

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

    def _handle_voice_message(self, phone: str, message_id: str, payload: dict) -> None:
        """Process voice message: Download -> STT -> AI -> TTS -> Voice response.

        Full voice pipeline:
        1. Download voice message from WAHA (try media.data first, then download API)
        2. Transcribe using ElevenLabs STT
        3. Get AI response (voice_mode=True for shorter text)
        4. Convert to speech using ElevenLabs TTS
        5. Send voice message via WAHA

        Falls back to text on any error.

        Args:
            phone: User's phone number
            message_id: WhatsApp message ID for downloading media
            payload: Full message payload from webhook
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

        # Step 1: Try ALL possible methods to get audio
        audio_bytes = None
        download_method = None

        # Log full payload structure for debugging
        logger.info(f"[WEBHOOK_HANDLER] Payload keys: {list(payload.keys())}")
        if "media" in payload:
            logger.info(f"[WEBHOOK_HANDLER] payload.media keys: {list(payload.get('media', {}).keys())}")
        if "_data" in payload:
            _data = payload.get("_data", {})
            logger.info(f"[WEBHOOK_HANDLER] payload._data keys: {list(_data.keys())}")
            if "message" in _data:
                logger.info(f"[WEBHOOK_HANDLER] payload._data.message keys: {list(_data.get('message', {}).keys())}")

        # Method 1: Try media.data from payload (base64 encoded)
        media_data = payload.get("media", {}).get("data")
        if media_data and not audio_bytes:
            logger.info(f"[WEBHOOK_HANDLER] METHOD 1: Trying media.data from payload (base64)")
            try:
                audio_bytes = base64.b64decode(media_data)
                download_method = "media.data (base64)"
                logger.info(f"[WEBHOOK_HANDLER] METHOD 1 SUCCESS: Got {len(audio_bytes)} bytes")
            except Exception as e:
                logger.warning(f"[WEBHOOK_HANDLER] METHOD 1 FAILED: {e}")

        # Method 2: Try media.url from payload (WAHA pre-signed URL)
        if not audio_bytes:
            media_url = payload.get("media", {}).get("url")
            if media_url:
                logger.info(f"[WEBHOOK_HANDLER] METHOD 2: Trying media.url: {media_url[:80]}...")
                try:
                    resp = requests.get(media_url, timeout=30)
                    if resp.ok:
                        audio_bytes = resp.content
                        download_method = "media.url"
                        logger.info(f"[WEBHOOK_HANDLER] METHOD 2 SUCCESS: Got {len(audio_bytes)} bytes")
                    else:
                        logger.warning(f"[WEBHOOK_HANDLER] METHOD 2 FAILED: HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"[WEBHOOK_HANDLER] METHOD 2 FAILED: {e}")

        # Method 3: Try mediaUrl from payload root
        if not audio_bytes:
            media_url_root = payload.get("mediaUrl")
            if media_url_root:
                logger.info(f"[WEBHOOK_HANDLER] METHOD 3: Trying mediaUrl from root: {media_url_root[:80]}...")
                try:
                    resp = requests.get(media_url_root, timeout=30)
                    if resp.ok:
                        audio_bytes = resp.content
                        download_method = "mediaUrl (root)"
                        logger.info(f"[WEBHOOK_HANDLER] METHOD 3 SUCCESS: Got {len(audio_bytes)} bytes")
                    else:
                        logger.warning(f"[WEBHOOK_HANDLER] METHOD 3 FAILED: HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"[WEBHOOK_HANDLER] METHOD 3 FAILED: {e}")

        # Method 4: Try WAHA download API with original message_id
        if not audio_bytes:
            logger.info(f"[WEBHOOK_HANDLER] METHOD 4: Trying WAHA download API with message_id: {message_id}")
            audio_bytes = self.waha.download_media(message_id)
            if audio_bytes:
                download_method = "WAHA download API"
                logger.info(f"[WEBHOOK_HANDLER] METHOD 4 SUCCESS: Got {len(audio_bytes)} bytes")
            else:
                logger.warning(f"[WEBHOOK_HANDLER] METHOD 4 FAILED")

        # Method 5: Try WAHA download API with @c.us format
        if not audio_bytes:
            message_id_cus = message_id.replace("@s.whatsapp.net", "@c.us")
            if message_id_cus != message_id:
                logger.info(f"[WEBHOOK_HANDLER] METHOD 5: Trying WAHA API with @c.us: {message_id_cus}")
                audio_bytes = self.waha.download_media(message_id_cus)
                if audio_bytes:
                    download_method = "WAHA download API (@c.us)"
                    logger.info(f"[WEBHOOK_HANDLER] METHOD 5 SUCCESS: Got {len(audio_bytes)} bytes")
                else:
                    logger.warning(f"[WEBHOOK_HANDLER] METHOD 5 FAILED")

        # Method 6: Try with just the message ID (no prefix)
        if not audio_bytes:
            # Extract raw ID from message_id (format: false_xxx@xxx_ACTUALID)
            parts = message_id.split("_")
            if len(parts) >= 3:
                raw_id = parts[-1]  # Last part is the actual message ID
                logger.info(f"[WEBHOOK_HANDLER] METHOD 6: Trying WAHA API with raw ID: {raw_id}")
                audio_bytes = self.waha.download_media(raw_id)
                if audio_bytes:
                    download_method = "WAHA download API (raw ID)"
                    logger.info(f"[WEBHOOK_HANDLER] METHOD 6 SUCCESS: Got {len(audio_bytes)} bytes")
                else:
                    logger.warning(f"[WEBHOOK_HANDLER] METHOD 6 FAILED")

        # Method 7: Try _data.message.audioMessage.url (WhatsApp encrypted URL - won't work directly but log it)
        if not audio_bytes:
            _data = payload.get("_data", {})
            message_content = _data.get("message", {})
            audio_msg = message_content.get("audioMessage", {})
            wa_url = audio_msg.get("url")
            if wa_url:
                logger.info(f"[WEBHOOK_HANDLER] METHOD 7: Found audioMessage.url (encrypted): {wa_url[:80]}...")
                # This is encrypted, can't download directly, but log for reference
                logger.warning(f"[WEBHOOK_HANDLER] METHOD 7: WhatsApp URL is encrypted, need WAHA to decrypt")

        if not audio_bytes:
            logger.error(f"[WEBHOOK_HANDLER] ALL METHODS FAILED for {masked_phone}")
            self._send_text(
                phone,
                "Не удалось загрузить голосовое сообщение. "
                "Попробуйте ещё раз или напишите текстом."
            )
            return

        logger.info(f"[WEBHOOK_HANDLER] SUCCESS via {download_method}: Got {len(audio_bytes)} bytes")

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
