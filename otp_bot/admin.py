from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html

from .admin_views import (
    OTPBotDisconnectView,
    OTPBotInitializeView,
    OTPBotManageView,
    OTPBotRefreshStatusView,
)
from .models import OTPBot, OTPCode


@admin.register(OTPBot)
class OTPBotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status_badge",
        "phone_number",
        "waha_session_name",
        "updated_at",
        "manage_button",
    )
    readonly_fields = ("id", "created_at", "updated_at", "management_panel")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/manage/",
                self.admin_site.admin_view(OTPBotManageView.as_view()),
                name="otp_bot_otpbot_manage",
            ),
            path(
                "<uuid:pk>/initialize/",
                self.admin_site.admin_view(OTPBotInitializeView.as_view()),
                name="otp_bot_otpbot_initialize",
            ),
            path(
                "<uuid:pk>/disconnect/",
                self.admin_site.admin_view(OTPBotDisconnectView.as_view()),
                name="otp_bot_otpbot_disconnect",
            ),
            path(
                "<uuid:pk>/refresh/",
                self.admin_site.admin_view(OTPBotRefreshStatusView.as_view()),
                name="otp_bot_otpbot_refresh",
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

    def manage_button(self, obj) -> str:
        """Link to management page in list view."""
        url = reverse("admin:otp_bot_otpbot_manage", args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#25D366; color:white; padding:5px 12px; '
            'border-radius:4px; text-decoration:none; font-size:12px; font-weight:bold;">'
            'Manage</a>',
            url,
        )
    manage_button.short_description = "Actions"

    def management_panel(self, obj) -> str:
        """Panel with manage button on change form."""
        if not obj.pk:
            return "Save first to access management."
        url = reverse("admin:otp_bot_otpbot_manage", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display:inline-block; background:#25D366; color:white; '
            'padding:10px 24px; border-radius:4px; text-decoration:none; '
            'font-size:14px; font-weight:bold;">Open Management Panel</a>',
            url,
        )
    management_panel.short_description = "Management"


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "phone_number", "is_used", "attempts_count", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("phone_number",)
    readonly_fields = ("id", "code_hash", "created_at")
