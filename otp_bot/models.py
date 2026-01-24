"""Models for OTP Bot service."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


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
        default="otp_service_bot",
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
