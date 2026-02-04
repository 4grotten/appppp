from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .admin_views import (
    OTPBotDeleteSessionView,
    OTPBotDisconnectView,
    OTPBotLogoutView,
    OTPBotQRCodeView,
    OTPBotRebindView,
    OTPBotStartSessionView,
    OTPBotStopSessionView,
)
from .models import OTPBot, OTPCode, ChatSession, UserVoicePreference, OTPBotPromptSettings


@admin.register(OTPBot)
class OTPBotAdmin(admin.ModelAdmin):
    list_display = (
        "waha_session_name",
        "status_badge",
        "phone_number",
        "updated_at",
    )
    readonly_fields = ("id", "status", "created_at", "updated_at", "actions_panel")
    fields = ("waha_session_name", "phone_number", "status", "actions_panel", "id", "created_at", "updated_at")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/start-session/",
                self.admin_site.admin_view(OTPBotStartSessionView.as_view()),
                name="otp_bot_otpbot_start_session",
            ),
            path(
                "<uuid:pk>/qr/",
                self.admin_site.admin_view(OTPBotQRCodeView.as_view()),
                name="otp_bot_otpbot_qr",
            ),
            path(
                "<uuid:pk>/disconnect/",
                self.admin_site.admin_view(OTPBotDisconnectView.as_view()),
                name="otp_bot_otpbot_disconnect",
            ),
            path(
                "<uuid:pk>/stop/",
                self.admin_site.admin_view(OTPBotStopSessionView.as_view()),
                name="otp_bot_otpbot_stop",
            ),
            path(
                "<uuid:pk>/logout/",
                self.admin_site.admin_view(OTPBotLogoutView.as_view()),
                name="otp_bot_otpbot_logout",
            ),
            path(
                "<uuid:pk>/delete-session/",
                self.admin_site.admin_view(OTPBotDeleteSessionView.as_view()),
                name="otp_bot_otpbot_delete_session",
            ),
            path(
                "<uuid:pk>/rebind/",
                self.admin_site.admin_view(OTPBotRebindView.as_view()),
                name="otp_bot_otpbot_rebind",
            ),
        ]
        return custom_urls + urls

    def status_badge(self, obj) -> str:
        """Colored status badge in list view."""
        colors = {
            "connected": ("#155724", "#d4edda"),
            "disconnected": ("#721c24", "#f8d7da"),
            "qr_pending": ("#856404", "#fff3cd"),
            "failed": ("#721c24", "#f5c6cb"),
        }
        color, bg = colors.get(obj.status, ("#333", "#eee"))
        return format_html(
            '<span style="color:{}; background:{}; padding:3px 8px; '
            'border-radius:10px; font-size:11px; font-weight:bold;">{}</span>',
            color, bg, obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    def actions_panel(self, obj) -> str:
        """Render action buttons on the change form based on bot status."""
        if not obj.pk:
            return "Save the bot first to see actions."

        buttons = []
        base_style = (
            "display: inline-block; padding: 10px 20px; margin: 5px; "
            "border-radius: 4px; text-decoration: none; font-weight: bold; "
            "color: white; font-size: 14px;"
        )

        if obj.status in ("disconnected", "failed"):
            url = reverse("admin:otp_bot_otpbot_start_session", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #25D366;">'
                f'Start Session</a>'
            )

        if obj.status == "qr_pending":
            url = reverse("admin:otp_bot_otpbot_qr", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #007bff;">'
                f'View QR Code</a>'
            )

        if obj.status == "connected":
            buttons.append(
                f'<span style="{base_style} background:#28a745; cursor:default;">'
                f'&#10003; Connected ({obj.phone_number or "unknown"})</span>'
            )
            # Rebind - change phone number
            url = reverse("admin:otp_bot_otpbot_rebind", args=[obj.pk])
            confirm_msg = "Change phone number? Current session will be disconnected and you will need to scan QR with the new phone."
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #17a2b8;" '
                f"onclick=\"return confirm('{confirm_msg}');\">"
                f'Rebind Number</a>'
            )

        # Session management buttons (always visible when session exists)
        if obj.status in ("connected", "qr_pending"):
            # Stop - keeps data, can restart
            url = reverse("admin:otp_bot_otpbot_stop", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #6c757d;" '
                f'onclick="return confirm(\'Stop the session? Can restart later.\');">'
                f'Stop</a>'
            )

            # Logout - requires QR re-scan
            url = reverse("admin:otp_bot_otpbot_logout", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #fd7e14;" '
                f'onclick="return confirm(\'Logout from WhatsApp? Will need QR scan to reconnect.\');">'
                f'Logout</a>'
            )

            # Delete - removes all session data
            url = reverse("admin:otp_bot_otpbot_delete_session", args=[obj.pk])
            buttons.append(
                f'<a href="{url}" style="{base_style} background: #dc3545;" '
                f'onclick="return confirm(\'DELETE session completely? All session data will be lost!\');">'
                f'Delete Session</a>'
            )

        return mark_safe("".join(buttons) if buttons else "No actions available.")
    actions_panel.short_description = "Session Actions"


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "phone_number", "is_used", "attempts_count", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("phone_number",)
    readonly_fields = ("id", "code_hash", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "message_count", "updated_at", "created_at")
    search_fields = ("phone_number",)
    readonly_fields = ("id", "messages", "created_at", "updated_at")
    ordering = ("-updated_at",)

    def message_count(self, obj) -> int:
        """Number of messages in the session."""
        return len(obj.messages) if obj.messages else 0
    message_count.short_description = "Messages"


@admin.register(UserVoicePreference)
class UserVoicePreferenceAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "voice_enabled", "updated_at")
    list_filter = ("voice_enabled",)
    search_fields = ("phone_number",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OTPBotPromptSettings)
class OTPBotPromptSettingsAdmin(admin.ModelAdmin):
    """Admin for OTP Bot AI prompts configuration (singleton)."""

    list_display = ["id", "is_active", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Status", {
            "fields": ("is_active",),
            "description": "If disabled, uses default prompts from prompts.py",
        }),
        ("Core Identity", {
            "fields": ("system_prompt_core",),
            "description": "Main AI personality and behavior instructions",
        }),
        ("EasyCard: About", {
            "fields": ("about_easycard", "card_types", "app_features"),
            "description": "General EasyCard information",
        }),
        ("EasyCard: Fees", {
            "fields": (
                "fees_one_time",
                "fees_topup",
                "fees_transfer",
                "fees_transactions",
            ),
            "classes": ("collapse",),
            "description": "Fee structure in AED",
        }),
        ("EasyCard: Rates & Notes", {
            "fields": ("exchange_rates", "important_notes"),
            "classes": ("collapse",),
        }),
        ("Business Scenarios", {
            "fields": (
                "scenario_new_user",
                "scenario_existing_user",
                "scenario_consultation",
                "scenario_escalation",
                "escalation_keywords",
            ),
            "description": "Scenario-based prompt templates",
        }),
        ("Voice Mode", {
            "fields": ("voice_mode_prompt", "voice_max_words"),
            "classes": ("collapse",),
            "description": "Settings for voice responses (TTS)",
        }),
        ("Language & Formatting", {
            "fields": ("language_detection_rule", "formatting_rules"),
            "classes": ("collapse",),
        }),
        ("WAHA Plus: Interactive Buttons", {
            "fields": ("buttons_config", "welcome_buttons"),
            "classes": ("collapse",),
            "description": "JSON configuration for interactive buttons/lists (requires WAHA Plus)",
        }),
        ("Error Messages", {
            "fields": ("error_ai", "error_timeout", "error_voice_unavailable"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        """Allow adding only if no records exist (singleton)."""
        return not OTPBotPromptSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of singleton."""
        return False
