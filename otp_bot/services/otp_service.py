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
from django.utils import timezone

from otp_bot.models import OTPBot, OTPBotStatus, OTPCode
from .waha_otp import WAHAOTPClient, WAHAOTPError

logger = logging.getLogger(__name__)

# Configuration defaults (overridable via Django settings)
OTP_CODE_TTL_SECONDS = getattr(settings, "OTP_CODE_TTL_SECONDS", 300)
OTP_MAX_ATTEMPTS = getattr(settings, "OTP_MAX_ATTEMPTS", 3)
OTP_RESEND_COOLDOWN_SECONDS = getattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 60)
OTP_MAX_PER_PHONE_10MIN = getattr(settings, "OTP_MAX_PER_PHONE_10MIN", 3)
OTP_MESSAGE_TEMPLATE = getattr(
    settings,
    "OTP_MESSAGE_TEMPLATE",
    "Ваш код подтверждения: {code}\n\nКод действителен {ttl_minutes} мин. Не сообщайте его никому.",
)


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

        Raises:
            BotNotConnectedError: If OTP bot is not connected
            RateLimitError: If rate limit exceeded
            OTPServiceError: If message sending fails
        """
        phone = self._validate_phone(phone_number)
        self._ensure_bot_connected()
        self._check_rate_limit(phone)

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

        # Send via WhatsApp
        message = OTP_MESSAGE_TEMPLATE.format(
            code=code,
            ttl_minutes=OTP_CODE_TTL_SECONDS // 60,
        )
        sent = self.waha.send_text(phone, message)

        if not sent:
            logger.error(f"[OTP] Failed to send OTP to {phone[:7]}***")
            # Don't delete the OTP — user can retry via resend
            raise OTPServiceError("Failed to send WhatsApp message")

        logger.info(f"[OTP] OTP sent to {phone[:7]}***: id={otp.id}")

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

    def _ensure_bot_connected(self) -> None:
        """Ensure OTP bot is connected and ready."""
        bot = OTPBot.objects.first()
        if not bot or bot.status != OTPBotStatus.CONNECTED:
            # Try quick health check
            if self.waha.is_healthy():
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
