"""Models for OTP Bot service."""

import logging
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import SingletonModel, TimestampModel

logger = logging.getLogger(__name__)


class OTPBotStatus(models.TextChoices):
    DISCONNECTED = "disconnected", _("Disconnected")
    QR_PENDING = "qr_pending", _("Waiting for QR scan")
    CONNECTED = "connected", _("Connected")
    FAILED = "failed", _("Failed")


class OTPBot(models.Model):
    """Singleton OTP bot — not tied to any organization.

    Manages a dedicated WAHA session for sending OTP codes.
    Only one instance should exist (enforced in service layer).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    waha_session_name = models.CharField(
        max_length=100,
        default="default",
        help_text=_("WAHA session name for OTP bot"),
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Connected WhatsApp phone number"),
    )
    status = models.CharField(
        max_length=20,
        choices=OTPBotStatus.choices,
        default=OTPBotStatus.DISCONNECTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("OTP Bot")
        verbose_name_plural = _("OTP Bots")

    def __str__(self) -> str:
        return f"OTP Bot [{self.status}] {self.phone_number or 'no phone'}"

    @property
    def is_connected(self) -> bool:
        return self.status == OTPBotStatus.CONNECTED


class OTPCode(models.Model):
    """OTP code sent to a phone number for verification.

    Stores only bcrypt hash of the code, never plaintext.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(
        max_length=20,
        db_index=True,
        help_text=_("Recipient phone number (E.164)"),
    )
    code_hash = models.CharField(
        max_length=128,
        help_text=_("Bcrypt hash of the OTP code"),
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text=_("When this OTP expires"),
    )
    attempts_count = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Number of verification attempts"),
    )
    is_used = models.BooleanField(
        default=False,
        help_text=_("Whether code was successfully verified"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("OTP Code")
        verbose_name_plural = _("OTP Codes")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["phone_number", "created_at"],
                name="idx_otp_phone_created",
            ),
        ]

    def __str__(self) -> str:
        status = "used" if self.is_used else "active"
        return f"OTP for {self.phone_number[:7]}*** [{status}]"


class ChatSession(models.Model):
    """Chat session for AI context preservation.

    Stores conversation history for maintaining context across messages.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_("User phone number (E.164)"),
    )
    messages = models.JSONField(
        default=list,
        help_text=_("Chat history: [{role, content}, ...]"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Chat Session")
        verbose_name_plural = _("Chat Sessions")
        indexes = [
            models.Index(fields=["phone_number", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"Chat {self.phone_number[:7]}*** ({len(self.messages)} msgs)"

    def add_message(self, role: str, content: str, max_messages: int = 10) -> None:
        """Add message to history, maintaining max limit.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            max_messages: Maximum number of messages to keep (FIFO)
        """
        self.messages.append({"role": role, "content": content})

        # Keep only last N messages
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

        self.save(update_fields=["messages", "updated_at"])

    def get_history(self) -> list:
        """Get chat history for AI context."""
        return self.messages.copy()

    def clear(self) -> None:
        """Clear chat history."""
        self.messages = []
        self.save(update_fields=["messages", "updated_at"])

    @classmethod
    def get_or_create_session(cls, phone_number: str) -> "ChatSession":
        """Get existing session or create new one.

        Args:
            phone_number: User's phone number (E.164 format)

        Returns:
            ChatSession instance
        """
        session, created = cls.objects.get_or_create(
            phone_number=phone_number,
            defaults={"messages": []},
        )
        if created:
            masked = phone_number[:7] + "***" if len(phone_number) > 7 else phone_number
            logger.info(f"[CHAT_SESSION] Created new session for {masked}")
        return session


class UserVoicePreference(models.Model):
    """User preference for voice responses.

    Controls whether the bot should always respond with voice
    or match the input type (text->text, voice->voice).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_("User phone number (E.164)"),
    )
    voice_enabled = models.BooleanField(
        default=False,
        help_text=_("If True, always respond with voice. If False, match input type."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Voice Preference")
        verbose_name_plural = _("User Voice Preferences")

    def __str__(self) -> str:
        status = "voice" if self.voice_enabled else "auto"
        return f"{self.phone_number[:7]}*** ({status})"

    @classmethod
    def get_preference(cls, phone_number: str) -> "UserVoicePreference":
        """Get or create voice preference for user.

        Args:
            phone_number: User's phone number (E.164 format)

        Returns:
            UserVoicePreference instance
        """
        pref, _ = cls.objects.get_or_create(
            phone_number=phone_number,
            defaults={"voice_enabled": False},
        )
        return pref

    def toggle(self) -> bool:
        """Toggle voice mode.

        Returns:
            New state (True = voice enabled, False = auto mode)
        """
        self.voice_enabled = not self.voice_enabled
        self.save(update_fields=["voice_enabled", "updated_at"])
        return self.voice_enabled


class OTPBotPromptSettings(TimestampModel, SingletonModel):
    """Singleton settings for OTP Bot AI prompts.

    Manages prompts for EasyCard Finance AI Assistant.
    Editable via Django Admin. Falls back to prompts.py defaults if not active.
    """

    # === Status ===
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("If disabled, uses default prompts from prompts.py"),
    )

    # === Core Identity ===
    system_prompt_core = models.TextField(
        default=(
            "Ты - дружелюбный AI-ассистент для финансового приложения Easy Card.\n"
            "Отвечай кратко и по делу на языке пользователя. Используй эмодзи для дружелюбности."
        ),
        verbose_name=_("Core System Prompt"),
        help_text=_("Main AI identity and behavior instructions"),
    )

    # === EasyCard Knowledge Base ===
    about_easycard = models.TextField(
        default=(
            "Easy Card - это финансовое приложение для управления "
            "виртуальными и металлическими картами в ОАЭ (валюта AED - дирхамы)."
        ),
        verbose_name=_("About Easy Card"),
        help_text=_("General description of EasyCard service"),
    )

    card_types = models.TextField(
        default=(
            "1. **Виртуальная карта** - мгновенный выпуск, идеально для онлайн-покупок\n"
            "2. **Металлическая карта** - премиум карта с доставкой, статусная и долговечная"
        ),
        verbose_name=_("Card Types"),
        help_text=_("Virtual and Metal card descriptions"),
    )

    fees_one_time = models.TextField(
        default=(
            "- Годовое обслуживание виртуальной карты: 183 AED\n"
            "- Перевыпуск виртуальной карты: 183 AED\n"
            "- Годовое обслуживание металлической карты: 183 AED\n"
            "- Перевыпуск металлической карты: 183 AED\n"
            "- Открытие виртуального счета: 183 AED"
        ),
        verbose_name=_("One-Time Fees"),
        help_text=_("Annual service, replacement fees in AED"),
    )

    fees_topup = models.TextField(
        default=(
            "- Криптовалютой (USDT): фиксированная комиссия 5.90 USDT\n"
            "- Банковским переводом: 1.5%\n"
            "- Минимальная сумма пополнения криптой: 15 USDT\n"
            "- Минимальная сумма пополнения банком: 50 AED"
        ),
        verbose_name=_("Top-Up Fees"),
        help_text=_("Crypto and bank transfer fees"),
    )

    fees_transfer = models.TextField(
        default=(
            "- С карты на карту: 1%\n"
            "- Банковский перевод: 2%\n"
            "- Сетевая комиссия: 1%"
        ),
        verbose_name=_("Transfer Fees"),
        help_text=_("Card-to-card, bank transfer, network fees"),
    )

    fees_transactions = models.TextField(
        default="- Конвертация валюты: 1.5%",
        verbose_name=_("Transaction Fees"),
        help_text=_("Currency conversion fees"),
    )

    exchange_rates = models.TextField(
        default=(
            "- Пополнение: 1 USDT = 3.65 AED\n"
            "- Вывод: 1 USDT = 3.69 AED"
        ),
        verbose_name=_("Exchange Rates"),
        help_text=_("USDT/AED rates for top-up and withdrawal"),
    )

    app_features = models.TextField(
        default=(
            "- Управление картами (виртуальные и металлические)\n"
            "- Пополнение баланса (криптой USDT или банковским переводом)\n"
            "- Переводы (на карту, на банк, криптой)\n"
            "- История транзакций\n"
            "- Настройка лимитов\n"
            "- Верификация личности (KYC)\n"
            "- Мультиязычность (EN, RU, AR, DE, ES, TR, ZH)"
        ),
        verbose_name=_("App Features"),
        help_text=_("List of EasyCard app capabilities"),
    )

    important_notes = models.TextField(
        default=(
            "- Все карты работают в валюте AED (дирхамы ОАЭ)\n"
            "- Для использования карт нужно пройти верификацию\n"
            "- Поддерживаются сети TRC20 и ERC20 для крипто-пополнений"
        ),
        verbose_name=_("Important Notes"),
        help_text=_("KYC requirements, supported networks, etc."),
    )

    # === Scenario Prompts ===
    scenario_new_user = models.TextField(
        default=(
            "Для новых пользователей (не зарегистрированных в EasyCard):\n"
            "- Приветствие с OTP кодом\n"
            "- Предложение перейти в чат EasyCard\n"
            "- После регистрации - предложение получить карту"
        ),
        verbose_name=_("Scenario: New User"),
        help_text=_("Instructions for users not in EasyCard DB"),
    )

    scenario_existing_user = models.TextField(
        default=(
            "Для существующих пользователей:\n"
            "- Отправка OTP кода\n"
            "- Консультация по приложению\n"
            "- Помощь с переводами и функциями"
        ),
        verbose_name=_("Scenario: Existing User"),
        help_text=_("Instructions for registered users"),
    )

    scenario_consultation = models.TextField(
        default=(
            "При консультации по EasyCard:\n"
            "- Отвечай на вопросы о картах, комиссиях, функциях\n"
            "- Помогай с навигацией по приложению\n"
            "- Если вопрос не про EasyCard - вежливо объясни свою специализацию"
        ),
        verbose_name=_("Scenario: Consultation"),
        help_text=_("AI consultation behavior instructions"),
    )

    scenario_escalation = models.TextField(
        default=(
            "Когда переводить на оператора:\n"
            "- Пользователь явно просит связаться с человеком\n"
            "- Сложные технические проблемы\n"
            "- Жалобы на работу сервиса\n"
            "- Вопросы, выходящие за рамки компетенции бота"
        ),
        verbose_name=_("Scenario: Escalation"),
        help_text=_("When to redirect to human operator"),
    )

    escalation_keywords = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Escalation Keywords"),
        help_text=_('Keywords triggering escalation, e.g. ["оператор", "человек", "помощь"]'),
    )

    # === Voice Mode ===
    voice_mode_prompt = models.TextField(
        default=(
            "РЕЖИМ ГОЛОСОВОГО ОТВЕТА:\n"
            "ВАЖНО: Этот ответ будет озвучен голосом, поэтому:\n"
            "- Отвечай ОЧЕНЬ кратко\n"
            "- Не используй списки, маркеры, форматирование\n"
            "- Не используй эмодзи\n"
            "- Говори естественно, как по телефону\n"
            "- Если нужна детальная информация - предложи написать текстом"
        ),
        verbose_name=_("Voice Mode Instructions"),
        help_text=_("Additional instructions for voice responses"),
    )

    voice_max_words = models.PositiveIntegerField(
        default=50,
        verbose_name=_("Voice Max Words"),
        help_text=_("Maximum words for voice responses"),
    )

    # === Language & Formatting ===
    language_detection_rule = models.TextField(
        default=(
            "Правила определения языка:\n"
            "1. Определяй язык из сообщения пользователя\n"
            "2. Отвечай на том же языке\n"
            "3. Если пользователь явно просит другой язык - переключись"
        ),
        verbose_name=_("Language Detection Rule"),
        help_text=_("How to detect and respond in user's language"),
    )

    formatting_rules = models.TextField(
        default=(
            "Правила форматирования:\n"
            "- Будь дружелюбным и полезным\n"
            "- Используй эмодзи умеренно для дружелюбности\n"
            "- Структурируй ответы для читаемости"
        ),
        verbose_name=_("Formatting Rules"),
        help_text=_("Emoji usage, message structure"),
    )

    # === WAHA Plus: Interactive Buttons ===
    buttons_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Buttons Configuration"),
        help_text=_("JSON config for WAHA Plus interactive buttons/lists"),
    )

    welcome_buttons = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Welcome Buttons"),
        help_text=_("Buttons for new user welcome message"),
    )

    # === Error Messages ===
    error_ai = models.TextField(
        default="Извините, произошла ошибка. Попробуйте позже.",
        verbose_name=_("AI Error Message"),
        help_text=_("Message shown when AI fails"),
    )

    error_timeout = models.TextField(
        default="Сервис не отвечает. Попробуйте позже.",
        verbose_name=_("Timeout Error Message"),
        help_text=_("Message shown on timeout"),
    )

    error_voice_unavailable = models.TextField(
        default="Голосовые сообщения временно недоступны. Напишите текстом.",
        verbose_name=_("Voice Unavailable Message"),
        help_text=_("Message when voice processing fails"),
    )

    # === OTP Messages ===
    otp_message_new_user = models.TextField(
        default=(
            "Здравствуйте! 👋\n\n"
            "Я ваш личный ассистент Easy Card 💳\n"
            "Помогу вам пройти регистрацию и отвечу на любые вопросы о картах, "
            "комиссиях и переводах.\n\n"
            "Ваш код подтверждения: {code}\n\n"
            "⏱ Код действителен {ttl_minutes} мин.\n"
            "🔒 Не сообщайте его никому."
        ),
        verbose_name=_("OTP Message (New User)"),
        help_text=_("Message sent with OTP code for first-time users. Use {code} and {ttl_minutes} placeholders."),
    )

    otp_message_existing_user = models.TextField(
        default=(
            "Ваш код подтверждения: {code}\n\n"
            "Код действителен {ttl_minutes} мин. Не сообщайте его никому."
        ),
        verbose_name=_("OTP Message (Existing User)"),
        help_text=_("Message sent with OTP code for returning users. Use {code} and {ttl_minutes} placeholders."),
    )

    welcome_message_after_registration = models.TextField(
        default=(
            "Отлично! Регистрация успешно завершена 🎉\n\n"
            "Добро пожаловать в Easy Card!\n\n"
            "Я всегда на связи и готов помочь:\n"
            "• Узнать баланс и историю операций\n"
            "• Рассказать о комиссиях и лимитах\n"
            "• Ответить на вопросы о картах\n\n"
            "Просто напишите мне! 💬"
        ),
        verbose_name=_("Welcome Message After Registration"),
        help_text=_("Message sent after successful OTP verification for new users."),
    )

    class Meta:
        verbose_name = _("OTP Bot Prompt Settings")
        verbose_name_plural = _("OTP Bot Prompt Settings")

    def __str__(self) -> str:
        return f"OTP Bot Prompt Settings (Active: {self.is_active})"

    @classmethod
    def get_settings(cls) -> "OTPBotPromptSettings":
        """Get or create singleton settings instance."""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
