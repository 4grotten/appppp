"""Models for OTP Bot service."""

import logging
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

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
