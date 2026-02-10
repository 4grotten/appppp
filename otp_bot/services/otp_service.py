"""OTP business logic service."""

import logging
import re
import secrets
import string
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import hashlib
import hmac

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from otp_bot.models import OTPBot, OTPBotStatus, OTPCode, OTPBotPromptSettings
from .waha_otp import WAHAOTPClient, WAHAOTPError

logger = logging.getLogger(__name__)

# Configuration defaults (overridable via Django settings)
OTP_CODE_TTL_SECONDS = getattr(settings, "OTP_CODE_TTL_SECONDS", 300)
OTP_MAX_ATTEMPTS = getattr(settings, "OTP_MAX_ATTEMPTS", 3)
OTP_RESEND_COOLDOWN_SECONDS = getattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 60)
OTP_MAX_PER_PHONE_10MIN = getattr(settings, "OTP_MAX_PER_PHONE_10MIN", 3)

# Fallback message templates (used if DB settings unavailable)
_FALLBACK_OTP_MESSAGE = "Ваш код подтверждения: {code}\n\nКод действителен {ttl_minutes} мин."
_FALLBACK_OTP_MESSAGE_NEW_USER = (
    "Здравствуйте! 👋\n\n"
    "Я ваш личный ассистент Easy Card 💳\n\n"
    "Ваш код подтверждения: {code}\n\n"
    "⏱ Код действителен {ttl_minutes} мин."
)
_FALLBACK_WELCOME_MESSAGE = "Добро пожаловать в Easy Card! 🎉"


def get_otp_message_templates() -> dict:
    """Get OTP message templates from DB settings with fallbacks."""
    try:
        prompt_settings = OTPBotPromptSettings.get_settings()
        return {
            "new_user": prompt_settings.otp_message_new_user or _FALLBACK_OTP_MESSAGE_NEW_USER,
            "existing_user": prompt_settings.otp_message_existing_user or _FALLBACK_OTP_MESSAGE,
            "welcome": prompt_settings.welcome_message_after_registration or _FALLBACK_WELCOME_MESSAGE,
        }
    except Exception as e:
        logger.warning(f"[OTP] Failed to load prompt settings: {e}, using fallbacks")
        return {
            "new_user": _FALLBACK_OTP_MESSAGE_NEW_USER,
            "existing_user": _FALLBACK_OTP_MESSAGE,
            "welcome": _FALLBACK_WELCOME_MESSAGE,
        }


class OTPServiceError(Exception):
    """Base OTP service error."""
    pass


class RateLimitError(OTPServiceError):
    """Rate limit exceeded."""
    pass


class CooldownError(OTPServiceError):
    """Resend cooldown not expired."""

    def __init__(self, seconds_remaining: int):
        self.seconds_remaining = seconds_remaining
        super().__init__(f"Cooldown: wait {seconds_remaining} seconds")


class BotNotConnectedError(OTPServiceError):
    """OTP bot is not connected."""
    pass


class VerificationError(OTPServiceError):
    """OTP verification failed."""
    pass


@dataclass
class SendOTPResult:
    otp_id: str
    phone_number: str
    expires_at: str
    sent: bool


@dataclass
class VerifyOTPResult:
    is_valid: bool
    error: Optional[str] = None


class OTPService:
    """Core OTP service — manages send, verify, resend logic."""

    def __init__(self, waha_client: Optional[WAHAOTPClient] = None) -> None:
        self.waha = waha_client or WAHAOTPClient()

    # --- Bot Management ---

    def initialize_bot(self) -> OTPBot:
        """Initialize OTP bot: create/get singleton, start WAHA session."""
        bot, created = OTPBot.objects.get_or_create(
            defaults={"status": OTPBotStatus.DISCONNECTED}
        )
        if created:
            logger.info(f"[OTP] Created new OTP bot: {bot.id}")

        # Start WAHA session
        success = self.waha.start_session()
        if success:
            bot.status = OTPBotStatus.QR_PENDING
            bot.save(update_fields=["status", "updated_at"])
            logger.info("[OTP] WAHA session started, waiting for QR scan")
        else:
            bot.status = OTPBotStatus.FAILED
            bot.save(update_fields=["status", "updated_at"])
            logger.error("[OTP] Failed to start WAHA session")

        return bot

    def get_bot_status(self) -> Optional[OTPBot]:
        """Get current OTP bot status, syncing with WAHA."""
        bot = OTPBot.objects.first()
        if not bot:
            return None

        # Sync status from WAHA
        waha_status = self.waha.get_session_status()
        new_status = self._map_waha_status(waha_status)

        if new_status != bot.status:
            bot.status = new_status
            # If connected, try to get phone number
            if new_status == OTPBotStatus.CONNECTED and not bot.phone_number:
                me = self.waha.get_me()
                if me:
                    phone = me.get("pushName") or me.get("id", "").split("@")[0]
                    if phone:
                        bot.phone_number = f"+{phone}" if not phone.startswith("+") else phone
            bot.save(update_fields=["status", "phone_number", "updated_at"])

        return bot

    def get_qr_code(self) -> Optional[str]:
        """Get QR code for bot authentication."""
        return self.waha.get_qr_code()

    def disconnect_bot(self) -> bool:
        """Disconnect OTP bot session."""
        bot = OTPBot.objects.first()
        if not bot:
            return False

        success = self.waha.stop_session()
        bot.status = OTPBotStatus.DISCONNECTED
        bot.phone_number = None
        bot.save(update_fields=["status", "phone_number", "updated_at"])
        logger.info("[OTP] Bot disconnected")
        return success

    # --- OTP Operations ---

    def send_otp(self, phone_number: str) -> SendOTPResult:
        """Generate and send OTP code to phone number.

        Validates phone format, checks rate limits, generates code,
        sends via WAHA, stores hash in DB.

        Uses personalized welcome message for first-time users.

        Raises:
            BotNotConnectedError: If OTP bot is not connected
            RateLimitError: If rate limit exceeded
            OTPServiceError: If message sending fails
        """
        phone = self._validate_phone(phone_number)
        self._ensure_bot_connected()

        # Combined query: rate limit + first OTP check (optimization #5)
        since = timezone.now() - timedelta(minutes=10)
        stats = OTPCode.objects.filter(phone_number=phone).aggregate(
            recent_count=Count('id', filter=Q(created_at__gte=since)),
            total_count=Count('id'),
        )

        if stats['recent_count'] >= OTP_MAX_PER_PHONE_10MIN:
            raise RateLimitError(
                f"Rate limit: max {OTP_MAX_PER_PHONE_10MIN} OTPs per 10 minutes"
            )

        is_first_otp = stats['total_count'] == 0

        # Generate 6-digit code
        code = self._generate_code()
        code_hash = self._hash_code(code)

        # Calculate expiry
        expires_at = timezone.now() + timedelta(seconds=OTP_CODE_TTL_SECONDS)

        # Save to DB (hash only)
        otp = OTPCode.objects.create(
            phone_number=phone,
            code_hash=code_hash,
            expires_at=expires_at,
        )

        # Get message templates from DB
        templates = get_otp_message_templates()
        template = templates["new_user"] if is_first_otp else templates["existing_user"]
        message = template.format(
            code=code,
            ttl_minutes=OTP_CODE_TTL_SECONDS // 60,
        )

        sent = self.waha.send_text(phone, message)

        if not sent:
            logger.error(f"[OTP] Failed to send OTP to {phone[:7]}***")
            # Don't delete the OTP — user can retry via resend
            raise OTPServiceError("Failed to send WhatsApp message")

        logger.info(f"[OTP] OTP sent to {phone[:7]}*** (first_otp={is_first_otp}): id={otp.id}")

        return SendOTPResult(
            otp_id=str(otp.id),
            phone_number=phone,
            expires_at=expires_at.isoformat(),
            sent=True,
        )

    def verify_otp(self, phone_number: str, code: str) -> VerifyOTPResult:
        """Verify an OTP code.

        Raises:
            VerificationError: If code is invalid, expired, or max attempts reached
        """
        phone = self._validate_phone(phone_number)

        # Get latest active OTP for this phone
        otp = (
            OTPCode.objects
            .filter(phone_number=phone, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return VerifyOTPResult(is_valid=False, error="No active OTP found")

        # Check expiry
        if otp.expires_at < timezone.now():
            return VerifyOTPResult(is_valid=False, error="OTP expired")

        # Check max attempts
        if otp.attempts_count >= OTP_MAX_ATTEMPTS:
            return VerifyOTPResult(is_valid=False, error="Max attempts exceeded")

        # Increment attempts
        otp.attempts_count += 1
        otp.save(update_fields=["attempts_count"])

        # Verify code against hash
        if not self._verify_code(code, otp.code_hash):
            remaining = OTP_MAX_ATTEMPTS - otp.attempts_count
            return VerifyOTPResult(
                is_valid=False,
                error=f"Invalid code. {remaining} attempts remaining",
            )

        # Success — mark as used
        otp.is_used = True
        otp.save(update_fields=["is_used"])

        logger.info(f"[OTP] Verified successfully for {phone[:7]}***")
        return VerifyOTPResult(is_valid=True)

    def resend_otp(self, phone_number: str) -> SendOTPResult:
        """Resend OTP with cooldown check.

        Raises:
            CooldownError: If cooldown period hasn't elapsed
        """
        phone = self._validate_phone(phone_number)

        # Check cooldown
        latest = (
            OTPCode.objects
            .filter(phone_number=phone)
            .order_by("-created_at")
            .first()
        )
        if latest:
            elapsed = (timezone.now() - latest.created_at).total_seconds()
            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                raise CooldownError(seconds_remaining=remaining)

        # Invalidate previous codes
        OTPCode.objects.filter(
            phone_number=phone, is_used=False
        ).update(is_used=True)

        # Send new OTP
        return self.send_otp(phone_number)

    def send_welcome_message(self, phone_number: str) -> bool:
        """Send welcome message after successful OTP verification for new users.

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            True if message was sent successfully, False otherwise
        """
        phone = self._validate_phone(phone_number)

        try:
            self._ensure_bot_connected()
        except BotNotConnectedError:
            logger.warning(f"[OTP] Cannot send welcome message - bot not connected")
            return False

        # Get welcome message from DB settings
        templates = get_otp_message_templates()
        welcome_message = templates["welcome"]

        sent = self.waha.send_text(phone, welcome_message)

        if sent:
            logger.info(f"[OTP] Welcome message sent to {phone[:7]}***")
        else:
            logger.error(f"[OTP] Failed to send welcome message to {phone[:7]}***")

        return sent

    # --- Private Helpers ---

    @staticmethod
    def _validate_phone(phone_number: str) -> str:
        """Validate and normalize phone number to E.164 format."""
        phone = phone_number.strip()
        if not re.match(r"^\+[1-9]\d{6,14}$", phone):
            raise OTPServiceError(
                f"Invalid phone format: must be E.164 (e.g., +79991234567)"
            )
        return phone

    def is_available(self) -> bool:
        """Check if OTP bot is connected and ready to send messages."""
        bot = OTPBot.objects.first()
        if not bot:
            return False
        if bot.status == OTPBotStatus.CONNECTED:
            return True
        # Try quick health check
        if self.waha.is_healthy():
            bot.status = OTPBotStatus.CONNECTED
            bot.save(update_fields=["status", "updated_at"])
            return True
        return False

    def _ensure_bot_connected(self) -> None:
        """Ensure OTP bot is connected and ready (with caching)."""
        # Quick cache check (5 sec TTL)
        if cache.get("otp_bot_connected"):
            return

        bot = OTPBot.objects.first()
        if bot and bot.status == OTPBotStatus.CONNECTED:
            cache.set("otp_bot_connected", True, timeout=5)
            return

        # Fallback to health check
        if self.waha.is_healthy():
            cache.set("otp_bot_connected", True, timeout=5)
            if bot:
                bot.status = OTPBotStatus.CONNECTED
                bot.save(update_fields=["status", "updated_at"])
            return

        raise BotNotConnectedError("OTP bot is not connected")

    @staticmethod
    def _check_rate_limit(phone: str) -> None:
        """Check rate limit: max N OTPs per phone in 10 minutes."""
        since = timezone.now() - timedelta(minutes=10)
        count = OTPCode.objects.filter(
            phone_number=phone,
            created_at__gte=since,
        ).count()
        if count >= OTP_MAX_PER_PHONE_10MIN:
            raise RateLimitError(
                f"Rate limit: max {OTP_MAX_PER_PHONE_10MIN} OTPs per 10 minutes"
            )

    @staticmethod
    def _generate_code() -> str:
        """Generate a cryptographically secure 6-digit code."""
        return "".join(secrets.choice(string.digits) for _ in range(6))

    @staticmethod
    def _hash_code(code: str) -> str:
        """Hash OTP code with HMAC-SHA256 using SECRET_KEY."""
        key = settings.SECRET_KEY.encode("utf-8")
        return hmac.new(key, code.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _verify_code(code: str, code_hash: str) -> bool:
        """Verify OTP code against HMAC-SHA256 hash."""
        key = settings.SECRET_KEY.encode("utf-8")
        computed = hmac.new(key, code.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, code_hash)

    @staticmethod
    def _map_waha_status(waha_status: str) -> str:
        """Map WAHA session status to OTPBot status."""
        mapping = {
            "WORKING": OTPBotStatus.CONNECTED,
            "AUTHENTICATED": OTPBotStatus.CONNECTED,
            "SCAN_QR_CODE": OTPBotStatus.QR_PENDING,
            "STARTING": OTPBotStatus.QR_PENDING,
            "FAILED": OTPBotStatus.FAILED,
            "STOPPED": OTPBotStatus.DISCONNECTED,
        }
        return mapping.get(waha_status.upper(), OTPBotStatus.DISCONNECTED)

    # --- Transaction Notifications ---

    def send_transaction_notification(
        self,
        phone_number: str,
        tx_type: str,
        amount: float,
        currency: str = "AED",
        merchant: Optional[str] = None,
        balance_after: Optional[float] = None,
    ) -> bool:
        """Send transaction notification via WhatsApp with interactive buttons.

        Formats and sends a push notification about a transaction event.
        Falls back to plain text if button sending fails.

        Args:
            phone_number: Phone number in E.164 format
            tx_type: Transaction type (top_up, card_payment, transfer_out, etc.)
            amount: Transaction amount
            currency: Currency code (default AED)
            merchant: Optional merchant name for payments
            balance_after: Optional balance after transaction

        Returns:
            True if notification was sent successfully
        """
        phone = self._validate_phone(phone_number)

        try:
            self._ensure_bot_connected()
        except BotNotConnectedError:
            logger.warning("[OTP] Cannot send transaction notification - bot not connected")
            return False

        # Emoji and text mapping for transaction types
        type_emoji = {
            "top_up": "💰",
            "card_payment": "🛒",
            "transfer_out": "📤",
            "transfer_in": "📥",
            "withdrawal": "🏧",
            "refund": "↩️",
            "fee": "📋",
            "cashback": "🎁",
            "card_activation": "💳",
        }

        type_text = {
            "top_up": "Пополнение",
            "card_payment": "Оплата",
            "transfer_out": "Перевод",
            "transfer_in": "Получен перевод",
            "withdrawal": "Снятие",
            "refund": "Возврат",
            "fee": "Комиссия",
            "cashback": "Кэшбэк",
            "card_activation": "Активация карты",
        }

        emoji = type_emoji.get(tx_type, "💳")
        action = type_text.get(tx_type, tx_type)

        # Determine sign for amount display
        positive_types = ("top_up", "transfer_in", "refund", "cashback")
        sign = "+" if tx_type in positive_types else "-"

        # Build message
        message = f"{emoji} {action}: {sign}{abs(amount):.2f} {currency}"

        if merchant:
            message += f"\n📍 {merchant}"

        if balance_after is not None:
            message += f"\n\n💰 Баланс: {balance_after:.2f} {currency}"

        # Get app URL from settings
        app_url = getattr(settings, "OTP_BOT_APP_URL", "https://easycarduae.com")

        # Interactive buttons (WAHA Plus format)
        buttons = [
            {"type": "reply", "id": "view_details", "text": "📊 Подробнее"},
            {"type": "url", "text": "📱 Открыть приложение", "url": app_url},
        ]

        # Try sending with interactive buttons first (WAHA Plus)
        sent = self.waha.send_interactive_buttons(phone, message, buttons)
        if not sent:
            logger.warning(f"[OTP] Buttons failed for {phone[:7]}***, falling back to text")
            sent = self.waha.send_text(phone, message)

        if sent:
            logger.info(f"[OTP] Transaction notification sent to {phone[:7]}***")
        else:
            logger.error(f"[OTP] Failed to send transaction notification to {phone[:7]}***")

        return sent

    def send_welcome_with_card_button(self, phone_number: str) -> bool:
        """Send welcome message with interactive buttons after registration.

        For new users who just completed registration, sends a welcome
        message with interactive buttons (URL/Call) for WAHA Plus.

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            True if message was sent successfully
        """
        phone = self._validate_phone(phone_number)

        try:
            self._ensure_bot_connected()
        except BotNotConnectedError:
            logger.warning("[OTP] Cannot send welcome with card button - bot not connected")
            return False

        # Get welcome message from DB settings
        templates = get_otp_message_templates()
        welcome_text = templates["welcome"]

        # Get URLs from settings
        cards_url = getattr(settings, "OTP_BOT_CARDS_URL", "https://easycarduae.com/cards")
        voice_url = getattr(
            settings,
            "OTP_BOT_VOICE_ASSISTANT_URL",
            "https://easycarduae.com/voice-assistant"
        )

        # Interactive buttons for new users (WAHA Plus format)
        buttons = [
            {"type": "url", "text": "💳 Забрать карту", "url": cards_url},
            {"type": "url", "text": "🎙 Голосовой ассистент", "url": voice_url},
            {"type": "reply", "id": "open_chat", "text": "💬 Начать чат"},
        ]

        # Try sending with interactive buttons first (WAHA Plus)
        sent = self.waha.send_interactive_buttons(phone, welcome_text, buttons)
        if not sent:
            # Fallback to text with URL
            text_with_link = f"{welcome_text}\n\n🔗 Забрать карту: {cards_url}"
            sent = self.waha.send_text(phone, text_with_link)

        if sent:
            logger.info(f"[OTP] Welcome with card button sent to {phone[:7]}***")
        else:
            logger.error(f"[OTP] Failed to send welcome with card button to {phone[:7]}***")

        return sent

    def send_otp_with_buttons(self, phone_number: str) -> SendOTPResult:
        """Generate and send OTP code with interactive buttons.

        Similar to send_otp() but includes interactive buttons appropriate
        for new vs existing users.

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            SendOTPResult with OTP details

        Raises:
            BotNotConnectedError: If OTP bot is not connected
            RateLimitError: If rate limit exceeded
            OTPServiceError: If message sending fails
        """
        phone = self._validate_phone(phone_number)
        self._ensure_bot_connected()
        self._check_rate_limit(phone)

        # Check if this is a new user (never received OTP before)
        is_first_otp = not OTPCode.objects.filter(phone_number=phone).exists()

        # Generate 6-digit code
        code = self._generate_code()
        code_hash = self._hash_code(code)

        # Calculate expiry
        expires_at = timezone.now() + timedelta(seconds=OTP_CODE_TTL_SECONDS)

        # Save to DB (hash only)
        otp = OTPCode.objects.create(
            phone_number=phone,
            code_hash=code_hash,
            expires_at=expires_at,
        )

        # Get message templates from DB
        templates = get_otp_message_templates()
        template = templates["new_user"] if is_first_otp else templates["existing_user"]
        message = template.format(
            code=code,
            ttl_minutes=OTP_CODE_TTL_SECONDS // 60,
        )

        # Buttons differ for new vs existing users
        if is_first_otp:
            buttons = [
                {"id": "open_chat", "text": "💬 Открыть чат EasyCard"},
                {"id": "about_service", "text": "ℹ️ О сервисе"},
            ]
        else:
            buttons = [
                {"id": "open_app", "text": "📱 Открыть приложение"},
            ]

        # Try buttons first, fallback to text
        sent = self.waha.send_buttons(phone, message, buttons)
        if not sent:
            logger.warning(f"[OTP] Buttons failed for {phone[:7]}***, falling back to text")
            sent = self.waha.send_text(phone, message)

        if not sent:
            logger.error(f"[OTP] Failed to send OTP to {phone[:7]}***")
            raise OTPServiceError("Failed to send WhatsApp message")

        logger.info(f"[OTP] OTP sent to {phone[:7]}*** (first_otp={is_first_otp}): id={otp.id}")

        return SendOTPResult(
            otp_id=str(otp.id),
            phone_number=phone,
            expires_at=expires_at.isoformat(),
            sent=True,
        )
