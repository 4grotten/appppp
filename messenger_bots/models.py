import secrets

from common.models import TimestampModel
from django.db import models
from django.utils.translation import gettext_lazy as _


class BotPlatform(models.TextChoices):
    TELEGRAM = "telegram", _("Telegram")
    WHATSAPP = "whatsapp", _("WhatsApp")


class WhatsAppProvider(models.TextChoices):
    WAHA = "waha", _("WAHA (Self-hosted)")
    TWILIO = "twilio", _("Twilio")
    META_CLOUD = "meta_cloud", _("Meta Cloud API")


class WhatsAppSessionStatus(models.TextChoices):
    PENDING = "pending", _("Pending QR Scan")
    SCAN_QR = "scan_qr", _("Scan QR Code")
    AUTHENTICATED = "authenticated", _("Authenticated")
    FAILED = "failed", _("Failed")
    DISCONNECTED = "disconnected", _("Disconnected")


class TelegramBot(TimestampModel):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="telegram_bot",
    )
    bot_token = models.CharField(
        max_length=100,
        help_text=_("Telegram Bot API token from @BotFather"),
    )
    bot_username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Bot username without @"),
    )
    webhook_secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("Secret token for webhook verification"),
    )
    is_active = models.BooleanField(default=True)
    webhook_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text=_("Webhook URL set on Telegram"),
    )
    last_error = models.TextField(
        null=True,
        blank=True,
        help_text=_("Last error message from Telegram API"),
    )

    class Meta:
        verbose_name = _("Telegram Bot")
        verbose_name_plural = _("Telegram Bots")

    def __str__(self):
        return f"Telegram Bot for {self.organization.title}"

    def save(self, *args, **kwargs):
        if not self.webhook_secret:
            self.webhook_secret = secrets.token_hex(32)
        super().save(*args, **kwargs)


class WhatsAppBot(TimestampModel):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="whatsapp_bot",
    )

    provider = models.CharField(
        max_length=20,
        choices=WhatsAppProvider.choices,
        default=WhatsAppProvider.WAHA,
        help_text=_("WhatsApp service provider"),
    )

    waha_session_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("WAHA session name (auto-generated as org_<id>)"),
    )
    session_status = models.CharField(
        max_length=20,
        choices=WhatsAppSessionStatus.choices,
        default=WhatsAppSessionStatus.PENDING,
        help_text=_("Current session status (for WAHA)"),
    )
    connected_phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Phone number connected via QR (for WAHA)"),
    )

    twilio_phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Twilio WhatsApp phone number"),
    )

    phone_number_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_("WhatsApp Business Phone Number ID (Meta Cloud)"),
    )
    business_account_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_("WhatsApp Business Account ID (Meta Cloud)"),
    )
    access_token = models.TextField(
        null=True,
        blank=True,
        help_text=_("Permanent access token from Meta Developer Portal"),
    )
    verify_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("Custom verification token for webhook setup"),
    )
    webhook_secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("App Secret for signature verification"),
    )
    display_phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Display phone number"),
    )

    is_active = models.BooleanField(default=True)
    last_error = models.TextField(
        null=True,
        blank=True,
        help_text=_("Last error message from WhatsApp API"),
    )
    last_activity_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last activity timestamp"),
    )

    class Meta:
        verbose_name = _("WhatsApp Bot")
        verbose_name_plural = _("WhatsApp Bots")

    def __str__(self):
        return f"WhatsApp Bot ({self.get_provider_display()}) for {self.organization.title}"

    def save(self, *args, **kwargs):
        if not self.verify_token:
            self.verify_token = secrets.token_hex(32)
        if self.provider == WhatsAppProvider.WAHA and not self.waha_session_name:
            self.waha_session_name = f"org_{self.organization_id}"
        super().save(*args, **kwargs)

    @property
    def is_connected(self) -> bool:
        if self.provider == WhatsAppProvider.WAHA:
            return self.session_status == WhatsAppSessionStatus.AUTHENTICATED
        return self.is_active


class BotChat(TimestampModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="bot_chats",
    )
    platform = models.CharField(
        max_length=20,
        choices=BotPlatform.choices,
    )
    platform_chat_id = models.CharField(
        max_length=100,
        help_text=_("Chat ID from the platform (Telegram chat_id or WhatsApp phone)"),
    )
    platform_user_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("User ID from the platform"),
    )
    user_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("User's name or username from the platform"),
    )
    user_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=_("User's phone number (for WhatsApp)"),
    )
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Bot Chat")
        verbose_name_plural = _("Bot Chats")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "platform", "platform_chat_id"),
                name="unique_bot_chat_per_org_platform",
            )
        ]

    def __str__(self):
        return f"{self.get_platform_display()} chat {self.platform_chat_id}"


class BotMessage(TimestampModel):
    USER = "user"
    ASSISTANT = "assistant"
    SENDER_TYPE = (
        (USER, _("User")),
        (ASSISTANT, _("Assistant")),
    )

    chat = models.ForeignKey(
        BotChat,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.CharField(
        max_length=25,
        choices=SENDER_TYPE,
        default=USER,
    )
    text = models.TextField()
    platform_message_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Message ID from the platform"),
    )

    class Meta:
        verbose_name = _("Bot Message")
        verbose_name_plural = _("Bot Messages")
        ordering = ("created_at",)

    def __str__(self):
        return f"Message from {self.sender} in chat {self.chat_id}"


class BotCreationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    IN_PROGRESS = "in_progress", _("In Progress")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")


class UserbotAuthState(models.TextChoices):
    NOT_STARTED = "not_started", _("Not Started")
    CODE_SENT = "code_sent", _("Code Sent")
    AWAITING_2FA = "awaiting_2fa", _("Awaiting 2FA Password")
    AUTHENTICATED = "authenticated", _("Authenticated")
    ERROR = "error", _("Error")


class TelegramUserbot(TimestampModel):
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        help_text=_(
            "Phone number of the Telegram account (with country code, e.g., +79001234567)"
        ),
    )
    api_id = models.CharField(
        max_length=20,
        help_text=_("Telegram API ID from my.telegram.org"),
    )
    api_hash = models.CharField(
        max_length=64,
        help_text=_("Telegram API Hash from my.telegram.org"),
    )
    session_string = models.TextField(
        null=True,
        blank=True,
        help_text=_("Telethon session string (generated after auth)"),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Is this userbot available for creating bots"),
    )
    is_authenticated = models.BooleanField(
        default=False,
        help_text=_("Has this userbot been authenticated"),
    )
    auth_state = models.CharField(
        max_length=20,
        choices=UserbotAuthState.choices,
        default=UserbotAuthState.NOT_STARTED,
        help_text=_("Current authentication state"),
    )
    phone_code_hash = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Phone code hash from Telegram (for auth flow)"),
    )
    auth_state_message = models.TextField(
        null=True,
        blank=True,
        help_text=_("Current authentication state message/instruction"),
    )

    bots_created_today = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of bots created today (BotFather limit ~20/day)"),
    )
    total_bots_created = models.PositiveIntegerField(
        default=0,
        help_text=_("Total number of bots created"),
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    last_error = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Telegram Userbot")
        verbose_name_plural = _("Telegram Userbots")

    def __str__(self):
        return f"Userbot {self.phone_number}"

    def reset_auth_state(self):
        self.auth_state = UserbotAuthState.NOT_STARTED
        self.phone_code_hash = None
        self.auth_state_message = None
        self.is_authenticated = False
        self.session_string = None


class BotCreationRequest(TimestampModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="bot_creation_requests",
    )
    requested_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="bot_creation_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=BotCreationStatus.choices,
        default=BotCreationStatus.PENDING,
    )
    bot_name = models.CharField(
        max_length=64,
        help_text=_("Desired bot name (e.g., 'OrgName APZ')"),
    )
    bot_username = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text=_("Generated bot username"),
    )
    bot_token = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Received bot token"),
    )
    userbot_used = models.ForeignKey(
        TelegramUserbot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="creation_requests",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    base_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Base URL for webhook (auto-detected from request)"),
    )

    class Meta:
        verbose_name = _("Bot Creation Request")
        verbose_name_plural = _("Bot Creation Requests")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Bot creation for {self.organization.title} - {self.status}"


class WhatsAppFailoverLog(TimestampModel):
    whatsapp_bot = models.ForeignKey(
        WhatsAppBot,
        on_delete=models.CASCADE,
        related_name="failover_logs",
    )
    from_provider = models.CharField(
        max_length=20,
        choices=WhatsAppProvider.choices,
        help_text=_("Provider before failover"),
    )
    to_provider = models.CharField(
        max_length=20,
        choices=WhatsAppProvider.choices,
        help_text=_("Provider after failover"),
    )
    reason = models.TextField(
        help_text=_("Reason for failover"),
    )

    class Meta:
        verbose_name = _("WhatsApp Failover Log")
        verbose_name_plural = _("WhatsApp Failover Logs")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Failover {self.from_provider} -> {self.to_provider} for {self.whatsapp_bot}"
