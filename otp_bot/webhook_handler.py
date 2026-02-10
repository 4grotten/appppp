"""Webhook handler for OTP Bot incoming messages.

Handles text and voice messages for the Finance AI Voice Assistant.
Voice flow: Download -> STT (ElevenLabs) -> AI -> TTS (ElevenLabs) -> Send Voice

Thread-safe singletons using functools.lru_cache.
Text message AI processing is offloaded to Celery for fast webhook response.

New user flow:
- First message from unregistered user -> Welcome + registration prompt
- Registered user -> Normal AI chat flow
"""

import logging
from functools import lru_cache

from django.core.cache import cache

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

        # Handle button response events
        if event == "message.button.response":
            self._handle_button_event(data)
            return

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
            # Check if this is a new unregistered user (first contact)
            if self._should_send_welcome(phone):
                self._send_welcome_unregistered(phone)
                # Still process commands after welcome
                if text.lower() not in ("/menu", "/start", "меню", "menu"):
                    return

            # Check for commands
            if text.lower() == "/voice":
                self._handle_voice_command(phone)
                return

            if text.lower() == "/clear":
                self._handle_clear_command(phone)
                return

            if text.lower() in ("/menu", "/start", "меню", "menu"):
                self._handle_menu_command(phone)
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

    def _handle_button_event(self, data: dict) -> None:
        """Handle button response event from WAHA.

        Args:
            data: Webhook payload with button response
        """
        payload = data.get("payload", {})

        # Skip our own messages
        if payload.get("fromMe"):
            return

        # Extract phone
        from_field = payload.get("from", "")
        if "@" in from_field:
            phone = from_field.split("@")[0]
        else:
            phone = from_field

        # Get button ID from response
        # WAHA format: payload.selectedButtonId or payload.button.id
        button_id = payload.get("selectedButtonId")
        if not button_id:
            button_response = payload.get("button", {})
            button_id = button_response.get("id") or button_response.get("selectedButtonId")

        if not button_id:
            # Try to extract from body text (some WAHA versions)
            body = payload.get("body", "")
            if body:
                # Button text might be in body, try to map it
                button_mapping = {
                    "Забрать карту": "get_card",
                    "Начать чат": "open_chat",
                    "Открыть приложение": "open_app",
                    "Подробнее": "view_details",
                    "О сервисе": "about_service",
                    "Открыть чат EasyCard": "open_chat",
                }
                for text, btn_id in button_mapping.items():
                    if text.lower() in body.lower():
                        button_id = btn_id
                        break

        if button_id:
            self.handle_button_response(phone, button_id, payload)
        else:
            logger.warning(f"[WEBHOOK_HANDLER] Could not extract button_id from payload")

    def _handle_text_message(self, phone: str, text: str) -> None:
        """Queue text message for async AI processing via Celery.

        AI calls can take 1-5 seconds which would block the webhook response.
        Offloading to Celery ensures fast webhook acknowledgment.
        Voice preference lookup moved to task for faster webhook response (optimization #6).

        Args:
            phone: User's phone number
            text: Message text
        """
        from .tasks import process_otp_text_message_task

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Text message from {masked_phone}, queuing task")

        # Offload immediately - voice_mode determined inside task
        process_otp_text_message_task.delay(
            phone=phone,
            text=text,
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

    def _handle_menu_command(self, phone: str) -> None:
        """Handle /menu command - show main menu with interactive buttons.

        Args:
            phone: User's phone number
        """
        from django.conf import settings

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Menu requested by {masked_phone}")

        # Send main menu with interactive buttons
        success = self.waha.send_menu(f"+{phone}")

        if not success:
            # Get URLs from settings for fallback
            voice_url = getattr(
                settings,
                "OTP_BOT_VOICE_ASSISTANT_URL",
                "https://easycarduae.com/voice-assistant"
            )
            cards_url = getattr(settings, "OTP_BOT_CARDS_URL", "https://easycarduae.com/cards")

            # Fallback to text menu
            self._send_text(
                phone,
                f"📋 *Главное меню*\n\n"
                f"🎙 Голосовой ассистент: {voice_url}\n"
                f"💳 Получить карту: {cards_url}\n\n"
                f"Или просто напишите ваш вопрос!"
            )

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

    def _should_send_welcome(self, phone: str) -> bool:
        """Check if we should send welcome message to this user.

        Returns True if:
        1. User has no chat history (first contact)
        2. User is not registered in EasyCard
        3. Welcome was not recently sent (cache check)

        Args:
            phone: User's phone number (without + prefix)

        Returns:
            True if welcome should be sent
        """
        # Check cache first (avoid sending welcome repeatedly)
        cache_key = f"otp_bot_welcome_sent_{phone}"
        if cache.get(cache_key):
            return False

        # Check if user has existing chat session with messages
        try:
            session = ChatSession.objects.filter(phone_number=phone).first()
            if session and session.messages:
                # User has chat history, not a new user
                return False
        except Exception as e:
            logger.warning(f"[WEBHOOK_HANDLER] Error checking chat session: {e}")

        # Check if user is registered in EasyCard
        if self._is_user_registered_in_easycard(phone):
            return False

        return True

    def _is_user_registered_in_easycard(self, phone: str) -> bool:
        """Check if user is registered in EasyCard database.

        Args:
            phone: User's phone number (without + prefix)

        Returns:
            True if user found in EasyCard database
        """
        try:
            from easycard_integration.services import EasyCardDataService

            # Try with + prefix
            data = EasyCardDataService.get_user_financial_data(f"+{phone}")
            if data.is_registered:
                return True

            # Try without + prefix
            data = EasyCardDataService.get_user_financial_data(phone)
            return data.is_registered

        except ImportError:
            logger.debug("[WEBHOOK_HANDLER] easycard_integration not available")
            return False
        except Exception as e:
            logger.warning(f"[WEBHOOK_HANDLER] Error checking EasyCard registration: {e}")
            return False

    def _send_welcome_unregistered(self, phone: str) -> None:
        """Send welcome message with registration prompt to unregistered user.

        Displays interactive buttons to guide new users to registration.

        Args:
            phone: User's phone number (without + prefix)
        """
        from django.conf import settings

        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Sending welcome to unregistered user {masked_phone}")

        # Mark welcome as sent (cache for 24 hours)
        cache_key = f"otp_bot_welcome_sent_{phone}"
        cache.set(cache_key, True, timeout=86400)

        # Get URLs from settings
        app_url = getattr(settings, "OTP_BOT_APP_URL", "https://easycarduae.com")
        voice_url = getattr(
            settings,
            "OTP_BOT_VOICE_ASSISTANT_URL",
            "https://easycarduae.com/voice-assistant"
        )

        welcome_text = (
            "👋 Здравствуйте!\n\n"
            "Я ваш персональный ассистент EasyCard — "
            "помогу с картами, переводами и ответами на вопросы.\n\n"
            "📱 Похоже, вы ещё не зарегистрированы в EasyCard.\n\n"
            "Пройдите быструю регистрацию, чтобы получить доступ "
            "ко всем возможностям:\n"
            "• 💳 Виртуальные и металлические карты\n"
            "• 💰 Пополнение криптой и переводами\n"
            "• 📊 История транзакций\n"
            "• 🎙 Голосовой ассистент"
        )

        # Interactive buttons for registration
        buttons = [
            {"type": "url", "text": "📱 Зарегистрироваться", "url": app_url},
            {"type": "url", "text": "🎙 Голосовой ассистент", "url": voice_url},
            {"type": "reply", "id": "ask_question", "text": "❓ Задать вопрос"},
        ]

        # Try interactive buttons first
        success = self.waha.send_interactive_buttons(
            f"+{phone}",
            welcome_text,
            buttons,
            footer="EasyCard UAE"
        )

        if not success:
            # Fallback to text
            fallback_text = (
                f"{welcome_text}\n\n"
                f"🔗 Регистрация: {app_url}\n"
                f"🎙 Голосовой ассистент: {voice_url}\n\n"
                "Или просто напишите ваш вопрос!"
            )
            self._send_text(phone, fallback_text)

        logger.info(f"[WEBHOOK_HANDLER] Welcome sent to {masked_phone}")

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

    # --- Button Response Handlers ---

    def handle_button_response(self, phone: str, button_id: str, payload: dict) -> None:
        """Handle interactive button response from user.

        Called when user clicks a button in an interactive message.
        Routes to appropriate handler based on button_id.

        Args:
            phone: User's phone number (without + prefix)
            button_id: ID of the clicked button
            payload: Full message payload from webhook
        """
        masked_phone = self._mask_phone(phone)
        logger.info(f"[WEBHOOK_HANDLER] Button response from {masked_phone}: {button_id}")

        handlers = {
            "open_chat": self._handle_open_chat,
            "start_chat": self._handle_start_chat,
            "ask_question": self._handle_ask_question,
            "open_app": self._handle_open_app,
            "get_card": self._handle_get_card,
            "view_details": self._handle_view_details,
            "about_service": self._handle_about_service,
        }

        handler = handlers.get(button_id)
        if handler:
            try:
                handler(phone, payload)
            except Exception as e:
                logger.error(
                    f"[WEBHOOK_HANDLER] Error handling button {button_id}: {e}",
                    exc_info=True,
                )
                self._send_text(phone, "Произошла ошибка. Попробуйте ещё раз.")
        else:
            logger.warning(f"[WEBHOOK_HANDLER] Unknown button: {button_id}")

    def _handle_get_card(self, phone: str, payload: dict) -> None:
        """Handle 'Get Card' button click.

        Provides instructions for obtaining an EasyCard.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        message = (
            "💳 Отлично! Для получения карты:\n\n"
            "1. Откройте приложение EasyCard\n"
            "2. Перейдите в раздел 'Карты'\n"
            "3. Выберите тип карты:\n"
            "   • Виртуальная — для онлайн-покупок\n"
            "   • Металлическая — премиум карта с доставкой\n\n"
            "🔗 https://easycarduae.com/cards"
        )
        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] Get card info sent to {self._mask_phone(phone)}")

    def _handle_open_chat(self, phone: str, payload: dict) -> None:
        """Handle 'Open Chat' button - redirect to EasyCard chat.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        message = (
            "💬 Чат EasyCard доступен в приложении!\n\n"
            "🔗 https://easycarduae.com/chat\n\n"
            "Или задайте вопрос прямо здесь — я помогу!"
        )
        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] Open chat info sent to {self._mask_phone(phone)}")

    def _handle_start_chat(self, phone: str, payload: dict) -> None:
        """Handle 'Start Chat' button - welcome to chat with AI assistant.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        message = (
            "💬 Отлично! Я готов помочь!\n\n"
            "Задайте любой вопрос о:\n"
            "• 💳 Картах и балансе\n"
            "• 💰 Пополнении и переводах\n"
            "• 📊 Транзакциях и истории\n"
            "• ❓ Любых других вопросах\n\n"
            "Просто напишите ваш вопрос!"
        )
        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] Start chat sent to {self._mask_phone(phone)}")

    def _handle_ask_question(self, phone: str, payload: dict) -> None:
        """Handle 'Ask Question' button - prompt for question from unregistered user.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        message = (
            "❓ Задайте ваш вопрос!\n\n"
            "Я могу помочь с информацией о:\n"
            "• 💳 Типах карт и их стоимости\n"
            "• 💰 Комиссиях и курсах обмена\n"
            "• 📱 Возможностях приложения\n"
            "• 🔐 Верификации и безопасности\n\n"
            "Просто напишите ваш вопрос, и я отвечу!"
        )
        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] Ask question prompt sent to {self._mask_phone(phone)}")

    def _handle_open_app(self, phone: str, payload: dict) -> None:
        """Handle 'Open App' button - provide app link.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        message = (
            "📱 Откройте приложение EasyCard:\n\n"
            "🔗 https://easycarduae.com\n\n"
            "Или установите из магазина приложений."
        )
        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] Open app info sent to {self._mask_phone(phone)}")

    def _handle_view_details(self, phone: str, payload: dict) -> None:
        """Handle 'View Details' button - show transaction details or balance.

        Fetches user's financial data from EasyCard and displays it.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        from easycard_integration.services import EasyCardDataService

        # Get user financial data
        data = EasyCardDataService.get_user_financial_data(f"+{phone}")

        if not data.is_registered:
            message = (
                "📊 Данные недоступны.\n\n"
                "Для просмотра деталей войдите в приложение:\n"
                "🔗 https://easycarduae.com"
            )
        else:
            # Format balance and recent transactions
            message = f"📊 Информация о вашем счёте:\n\n"
            message += f"💰 Общий баланс: {data.total_balance:.2f} AED\n"

            if data.cards:
                message += f"\n💳 Карты: {len(data.cards)}\n"
                for card in data.cards[:3]:  # Show max 3 cards
                    status_emoji = "✅" if card["status"] == "active" else "⏸️"
                    message += f"  {status_emoji} {card['name']}: {card['balance']:.2f} AED\n"

            if data.recent_transactions:
                message += f"\n📜 Последние операции:\n"
                for tx in data.recent_transactions[:3]:  # Show max 3 transactions
                    date_str = tx["created_at"].strftime("%d.%m")
                    message += f"  • {date_str}: {tx['amount']:.2f} AED\n"

            message += "\n🔗 https://easycarduae.com"

        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] View details sent to {self._mask_phone(phone)}")

    def _handle_about_service(self, phone: str, payload: dict) -> None:
        """Handle 'About Service' button - provide service information.

        Args:
            phone: User's phone number
            payload: Message payload
        """
        message = (
            "ℹ️ О сервисе Easy Card\n\n"
            "Easy Card — финансовое приложение для управления "
            "виртуальными и металлическими картами в ОАЭ.\n\n"
            "✨ Возможности:\n"
            "• Виртуальные и металлические карты\n"
            "• Пополнение криптой (USDT) или переводом\n"
            "• Переводы между картами\n"
            "• История транзакций\n"
            "• Мультиязычный интерфейс\n\n"
            "💱 Валюта: AED (дирхамы ОАЭ)\n\n"
            "🔗 https://easycarduae.com"
        )
        self._send_text(phone, message)
        logger.info(f"[WEBHOOK_HANDLER] About service sent to {self._mask_phone(phone)}")
