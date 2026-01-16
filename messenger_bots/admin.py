from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from messenger_bots.models import (
    TelegramBot,
    WhatsAppBot,
    WhatsAppProvider,
    WhatsAppSessionStatus,
    WhatsAppFailoverLog,
    BotChat,
    BotMessage,
    TelegramUserbot,
    BotCreationRequest,
    BotCreationStatus,
    UserbotAuthState,
)
from messenger_bots.admin_views import (
    UserbotSendCodeView,
    UserbotVerifyCodeView,
    UserbotQRLoginView,
    UserbotVerify2FAView,
    UserbotCheckConnectionView,
    UserbotLogoutView,
    UserbotDialogsView,
    UserbotTestMessageView,
)


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "bot_username",
        "is_active",
        "context_messages_limit",
        "status_indicator",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["organization__title", "bot_username"]
    readonly_fields = ["webhook_secret", "webhook_url", "last_error", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("organization", "bot_token", "is_active")
        }),
        ("AI Context Settings", {
            "fields": ("context_messages_limit",),
            "description": "Количество пар сообщений (user+assistant) для контекста AI. "
                          "Например: 5 = последние 10 сообщений (5 от пользователя + 5 от бота).",
        }),
        ("Bot Info", {
            "fields": ("bot_username", "webhook_url"),
            "classes": ("collapse",),
        }),
        ("Security", {
            "fields": ("webhook_secret",),
            "classes": ("collapse",),
        }),
        ("Status", {
            "fields": ("last_error", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def status_indicator(self, obj):
        if obj.last_error:
            return format_html(
                '<span style="color: red;">⚠️ Error</span>'
            )
        if obj.is_active and obj.webhook_url:
            return format_html(
                '<span style="color: green;">✅ Active</span>'
            )
        return format_html(
            '<span style="color: orange;">⏸️ Inactive</span>'
        )
    status_indicator.short_description = "Status"


@admin.register(WhatsAppBot)
class WhatsAppBotAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "provider_badge",
        "phone_display",
        "is_active",
        "connection_status",
        "last_activity_at",
        "created_at",
    ]
    list_filter = ["provider", "is_active", "session_status", "created_at"]
    search_fields = [
        "organization__title",
        "display_phone_number",
        "connected_phone_number",
        "phone_number_id",
        "waha_session_name",
    ]
    readonly_fields = [
        "verify_token",
        "waha_session_name",
        "session_status",
        "connected_phone_number",
        "display_phone_number",
        "last_error",
        "last_activity_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {
            "fields": ("organization", "provider", "is_active")
        }),
        ("WAHA Configuration (Self-hosted)", {
            "fields": (
                "waha_session_name",
                "session_status",
                "connected_phone_number",
            ),
            "classes": ("collapse",),
            "description": "Settings for WAHA (WhatsApp HTTP API) provider",
        }),
        ("Meta Cloud API Configuration", {
            "fields": (
                "phone_number_id",
                "business_account_id",
                "access_token",
                "display_phone_number",
            ),
            "classes": ("collapse",),
            "description": "Settings for Meta Cloud API provider",
        }),
        ("Twilio Configuration", {
            "fields": ("twilio_phone_number",),
            "classes": ("collapse",),
            "description": "Settings for Twilio provider (not yet implemented)",
        }),
        ("Webhook & Security", {
            "fields": ("verify_token", "webhook_secret"),
            "classes": ("collapse",),
        }),
        ("Status", {
            "fields": ("last_error", "last_activity_at", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def provider_badge(self, obj):
        """Show provider as a colored badge."""
        colors = {
            WhatsAppProvider.WAHA: "#28a745",  # green
            WhatsAppProvider.TWILIO: "#dc3545",  # red
            WhatsAppProvider.META_CLOUD: "#007bff",  # blue
        }
        color = colors.get(obj.provider, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_provider_display()
        )
    provider_badge.short_description = "Provider"

    def phone_display(self, obj):
        """Show the relevant phone number based on provider."""
        if obj.provider == WhatsAppProvider.WAHA:
            return obj.connected_phone_number or "Not connected"
        elif obj.provider == WhatsAppProvider.TWILIO:
            return obj.twilio_phone_number or "Not set"
        else:
            return obj.display_phone_number or obj.phone_number_id or "Not set"
    phone_display.short_description = "Phone"

    def connection_status(self, obj):
        """Show connection status with appropriate indicator."""
        if obj.last_error:
            return format_html(
                '<span style="color: red;" title="{}">⚠️ Error</span>',
                obj.last_error[:100]
            )

        if obj.provider == WhatsAppProvider.WAHA:
            status_colors = {
                WhatsAppSessionStatus.PENDING: ("orange", "⏳"),
                WhatsAppSessionStatus.SCAN_QR: ("blue", "📱"),
                WhatsAppSessionStatus.AUTHENTICATED: ("green", "✅"),
                WhatsAppSessionStatus.FAILED: ("red", "❌"),
                WhatsAppSessionStatus.DISCONNECTED: ("gray", "⏸️"),
            }
            color, icon = status_colors.get(obj.session_status, ("gray", "?"))
            return format_html(
                '<span style="color: {};">{} {}</span>',
                color, icon, obj.get_session_status_display()
            )

        # For other providers
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Active</span>')
        return format_html('<span style="color: orange;">⏸️ Inactive</span>')
    connection_status.short_description = "Status"


@admin.register(BotChat)
class BotChatAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "organization",
        "platform",
        "user_name",
        "user_phone",
        "messages_count",
        "last_message_at",
        "is_active",
    ]
    list_filter = ["platform", "is_active", "created_at"]
    search_fields = ["organization__title", "user_name", "user_phone", "platform_chat_id"]
    readonly_fields = [
        "platform_chat_id",
        "platform_user_id",
        "created_at",
        "updated_at",
        "last_message_at",
    ]

    def messages_count(self, obj):
        return obj.messages.count()
    messages_count.short_description = "Messages"


@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "chat",
        "sender",
        "text_preview",
        "created_at",
    ]
    list_filter = ["sender", "created_at", "chat__platform"]
    search_fields = ["text", "chat__user_name"]
    readonly_fields = ["chat", "sender", "text", "platform_message_id", "created_at"]

    def text_preview(self, obj):
        if len(obj.text) > 50:
            return obj.text[:50] + "..."
        return obj.text
    text_preview.short_description = "Text"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(TelegramUserbot)
class TelegramUserbotAdmin(admin.ModelAdmin):
    """Admin for managing Telegram userbots that create bots via BotFather."""

    list_display = [
        "phone_number",
        "is_active",
        "auth_status_badge",
        "bots_created_today",
        "total_bots_created",
        "status_indicator",
        "action_buttons",
        "last_used_at",
    ]
    list_filter = ["is_active", "is_authenticated", "auth_state"]
    search_fields = ["phone_number"]
    readonly_fields = [
        "session_string",
        "is_authenticated",
        "auth_state",
        "auth_state_message",
        "phone_code_hash",
        "bots_created_today",
        "total_bots_created",
        "last_used_at",
        "last_error",
        "created_at",
        "updated_at",
        "auth_actions_panel",
        "debug_actions_panel",
    ]

    fieldsets = (
        (None, {
            "fields": ("phone_number", "is_active")
        }),
        ("Telegram API Credentials", {
            "fields": ("api_id", "api_hash"),
            "description": "Get these from https://my.telegram.org",
        }),
        ("Authentication Actions", {
            "fields": ("auth_actions_panel",),
            "description": "Use these buttons to authenticate the userbot",
        }),
        ("Authentication Status", {
            "fields": ("is_authenticated", "auth_state", "auth_state_message"),
        }),
        ("Debug & Testing", {
            "fields": ("debug_actions_panel",),
            "classes": ("collapse",),
            "description": "Debug and testing tools",
        }),
        ("Session Data", {
            "fields": ("session_string", "phone_code_hash"),
            "classes": ("collapse",),
        }),
        ("Statistics", {
            "fields": ("bots_created_today", "total_bots_created", "last_used_at", "last_error"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_urls(self):
        """Add custom URLs for userbot management."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/send-code/",
                self.admin_site.admin_view(UserbotSendCodeView.as_view()),
                name="messenger_bots_userbot_send_code",
            ),
            path(
                "<int:pk>/verify-code/",
                self.admin_site.admin_view(UserbotVerifyCodeView.as_view()),
                name="messenger_bots_userbot_verify_code",
            ),
            path(
                "<int:pk>/qr-login/",
                self.admin_site.admin_view(UserbotQRLoginView.as_view()),
                name="messenger_bots_userbot_qr_login",
            ),
            path(
                "<int:pk>/verify-2fa/",
                self.admin_site.admin_view(UserbotVerify2FAView.as_view()),
                name="messenger_bots_userbot_verify_2fa",
            ),
            path(
                "<int:pk>/check-connection/",
                self.admin_site.admin_view(UserbotCheckConnectionView.as_view()),
                name="messenger_bots_userbot_check_connection",
            ),
            path(
                "<int:pk>/logout/",
                self.admin_site.admin_view(UserbotLogoutView.as_view()),
                name="messenger_bots_userbot_logout",
            ),
            path(
                "<int:pk>/dialogs/",
                self.admin_site.admin_view(UserbotDialogsView.as_view()),
                name="messenger_bots_userbot_dialogs",
            ),
            path(
                "<int:pk>/test-message/",
                self.admin_site.admin_view(UserbotTestMessageView.as_view()),
                name="messenger_bots_userbot_test_message",
            ),
        ]
        return custom_urls + urls

    def auth_status_badge(self, obj):
        """Show authentication state as a badge."""
        badges = {
            UserbotAuthState.NOT_STARTED: ("gray", "Not Started"),
            UserbotAuthState.CODE_SENT: ("orange", "Code Sent"),
            UserbotAuthState.AWAITING_2FA: ("blue", "Awaiting 2FA"),
            UserbotAuthState.AUTHENTICATED: ("green", "Authenticated"),
            UserbotAuthState.ERROR: ("red", "Error"),
        }
        color, text = badges.get(obj.auth_state, ("gray", "Unknown"))
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 11px; font-weight: bold;">{}</span>',
            color, text
        )
    auth_status_badge.short_description = "Auth State"

    def status_indicator(self, obj):
        if not obj.is_authenticated:
            return format_html(
                '<span style="color: red;">Not Ready</span>'
            )
        if obj.bots_created_today >= 20:
            return format_html(
                '<span style="color: orange;">Daily Limit</span>'
            )
        if obj.is_active:
            return format_html(
                '<span style="color: green;">Ready ({}/20)</span>',
                obj.bots_created_today
            )
        return format_html(
            '<span style="color: gray;">Inactive</span>'
        )
    status_indicator.short_description = "Status"

    def action_buttons(self, obj):
        """Show quick action buttons in list view."""
        if not obj.pk:
            return "-"

        buttons = []

        if not obj.is_authenticated:
            # Show authenticate button
            url = reverse("admin:messenger_bots_userbot_send_code", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="background: #28a745; color: white; '
                f'padding: 3px 8px; border-radius: 4px; text-decoration: none; '
                f'font-size: 11px; margin-right: 5px;">Authenticate</a>'
            )
        else:
            # Show check connection button
            url = reverse("admin:messenger_bots_userbot_check_connection", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="background: #007bff; color: white; '
                f'padding: 3px 8px; border-radius: 4px; text-decoration: none; '
                f'font-size: 11px; margin-right: 5px;">Check</a>'
            )

        return mark_safe("".join(buttons))
    action_buttons.short_description = "Actions"

    def auth_actions_panel(self, obj):
        """Render authentication action buttons."""
        if not obj.pk:
            return "Save the userbot first to see authentication actions."

        buttons = []
        base_style = (
            "display: inline-block; padding: 10px 20px; margin: 5px; "
            "border-radius: 4px; text-decoration: none; font-weight: bold; "
            "color: white; font-size: 14px;"
        )

        if not obj.is_authenticated:
            # Authentication flow buttons based on state
            if obj.auth_state == UserbotAuthState.NOT_STARTED:
                # QR Login (recommended)
                url = reverse("admin:messenger_bots_userbot_qr_login", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #28a745;">'
                    f'Login via QR Code (Recommended)</a>'
                )
                # Phone code (alternative)
                url = reverse("admin:messenger_bots_userbot_send_code", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #6c757d;">'
                    f'Login via Phone Code</a>'
                )
            elif obj.auth_state == UserbotAuthState.CODE_SENT:
                url = reverse("admin:messenger_bots_userbot_verify_code", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #007bff;">'
                    f'2. Enter Code</a>'
                )
                # Also show QR option
                url = reverse("admin:messenger_bots_userbot_qr_login", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #28a745;">'
                    f'Try QR Login Instead</a>'
                )
            elif obj.auth_state == UserbotAuthState.AWAITING_2FA:
                url = reverse("admin:messenger_bots_userbot_verify_2fa", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #17a2b8;">'
                    f'3. Enter 2FA Password</a>'
                )
            elif obj.auth_state == UserbotAuthState.ERROR:
                url = reverse("admin:messenger_bots_userbot_qr_login", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #28a745;">'
                    f'Retry via QR Code</a>'
                )
                url = reverse("admin:messenger_bots_userbot_send_code", args=[obj.pk])
                buttons.append(
                    f'<a href="{url}" style="{base_style} background: #dc3545;">'
                    f'Retry via Phone Code</a>'
                )
        else:
            # Already authenticated - show logout option
            url = reverse("admin:messenger_bots_userbot_check_connection", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #28a745;">'
                f'Check Connection</a>'
            )
            url = reverse("admin:messenger_bots_userbot_logout", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #dc3545;">'
                f'Logout</a>'
            )

        return mark_safe("".join(buttons) if buttons else "No actions available")
    auth_actions_panel.short_description = "Authentication Actions"

    def debug_actions_panel(self, obj):
        """Render debug action buttons."""
        if not obj.pk:
            return "Save the userbot first."

        if not obj.is_authenticated:
            return "Authenticate first to access debug tools."

        buttons = []
        base_style = (
            "display: inline-block; padding: 8px 15px; margin: 5px; "
            "border-radius: 4px; text-decoration: none; font-weight: bold; "
            "color: white; font-size: 13px;"
        )

        url = reverse("admin:messenger_bots_userbot_dialogs", args=[obj.pk])
        buttons.append(
            f'<a href="{url}" style="{base_style} background: #6f42c1;">'
            f'View Dialogs</a>'
        )

        url = reverse("admin:messenger_bots_userbot_test_message", args=[obj.pk])
        buttons.append(
            f'<a href="{url}" style="{base_style} background: #fd7e14;">'
            f'Send Test Message</a>'
        )

        return mark_safe("".join(buttons))
    debug_actions_panel.short_description = "Debug & Testing"

    actions = ["reset_daily_counter", "reset_auth_state"]

    def reset_daily_counter(self, request, queryset):
        updated = queryset.update(bots_created_today=0)
        self.message_user(request, f"Reset counter for {updated} userbot(s).")
    reset_daily_counter.short_description = "Reset daily bot creation counter"

    def reset_auth_state(self, request, queryset):
        for userbot in queryset:
            userbot.reset_auth_state()
            userbot.save()
        self.message_user(
            request,
            f"Reset authentication state for {queryset.count()} userbot(s). "
            "They need to be re-authenticated."
        )
    reset_auth_state.short_description = "Reset authentication state (for re-auth)"


@admin.register(BotCreationRequest)
class BotCreationRequestAdmin(admin.ModelAdmin):
    """Admin for viewing bot creation requests."""

    list_display = [
        "id",
        "organization",
        "bot_name",
        "status_indicator",
        "bot_username",
        "requested_by",
        "created_at",
        "completed_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["organization__title", "bot_name", "bot_username"]
    readonly_fields = [
        "organization",
        "requested_by",
        "bot_name",
        "bot_username",
        "bot_token",
        "userbot_used",
        "status",
        "error_message",
        "created_at",
        "completed_at",
    ]

    fieldsets = (
        (None, {
            "fields": ("organization", "requested_by", "status")
        }),
        ("Bot Details", {
            "fields": ("bot_name", "bot_username", "bot_token"),
        }),
        ("Processing", {
            "fields": ("userbot_used", "error_message"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "completed_at"),
            "classes": ("collapse",),
        }),
    )

    def status_indicator(self, obj):
        colors = {
            BotCreationStatus.PENDING: ("orange", "⏳"),
            BotCreationStatus.IN_PROGRESS: ("blue", "🔄"),
            BotCreationStatus.COMPLETED: ("green", "✅"),
            BotCreationStatus.FAILED: ("red", "❌"),
        }
        color, icon = colors.get(obj.status, ("gray", "?"))
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_indicator.short_description = "Status"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WhatsAppFailoverLog)
class WhatsAppFailoverLogAdmin(admin.ModelAdmin):
    """Admin for viewing WhatsApp failover logs."""

    list_display = [
        "id",
        "whatsapp_bot",
        "failover_direction",
        "reason_preview",
        "created_at",
    ]
    list_filter = ["from_provider", "to_provider", "created_at"]
    search_fields = ["whatsapp_bot__organization__title", "reason"]
    readonly_fields = [
        "whatsapp_bot",
        "from_provider",
        "to_provider",
        "reason",
        "created_at",
    ]

    def failover_direction(self, obj):
        """Show failover direction with arrow."""
        return format_html(
            '{} → {}',
            obj.get_from_provider_display(),
            obj.get_to_provider_display()
        )
    failover_direction.short_description = "Failover"

    def reason_preview(self, obj):
        """Show truncated reason."""
        if len(obj.reason) > 50:
            return obj.reason[:50] + "..."
        return obj.reason
    reason_preview.short_description = "Reason"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
