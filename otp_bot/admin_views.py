"""Custom admin views for OTP Bot management."""

import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from otp_bot.models import OTPBot
from otp_bot.services.otp_service import OTPService

logger = logging.getLogger(__name__)


class OTPBotManageBaseView(View):
    """Base view for OTP bot admin actions."""

    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.bot = get_object_or_404(OTPBot, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_changelist_url(self) -> str:
        return reverse("admin:otp_bot_otpbot_changelist")

    def get_manage_url(self) -> str:
        return reverse("admin:otp_bot_otpbot_manage", args=[self.bot.pk])


class OTPBotManageView(OTPBotManageBaseView):
    """Main management page — shows status, QR, and action buttons."""

    template_name = "admin/otp_bot/management.html"

    def get(self, request, pk):
        service = OTPService()

        # Sync status from WAHA
        bot = service.get_bot_status()
        if bot:
            self.bot = bot

        # Get QR code if pending
        qr_code = None
        if self.bot.status == "qr_pending":
            qr_code = service.get_qr_code()

        context = {
            "bot": self.bot,
            "qr_code": qr_code,
            "title": "OTP Bot Management",
            "site_header": "Apofiz Administration",
            "has_view_permission": True,
        }
        return render(request, self.template_name, context)


class OTPBotInitializeView(OTPBotManageBaseView):
    """Initialize or restart OTP bot WAHA session."""

    def post(self, request, pk):
        service = OTPService()
        try:
            bot = service.initialize_bot()
            if bot.status == "qr_pending":
                messages.success(request, "Session started. Scan the QR code with WhatsApp.")
            elif bot.status == "connected":
                messages.success(request, "Bot is already connected.")
            else:
                messages.error(request, f"Initialization failed. Status: {bot.status}")
        except Exception as e:
            logger.exception("[OTP Admin] Initialize failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_manage_url())


class OTPBotDisconnectView(OTPBotManageBaseView):
    """Disconnect OTP bot session."""

    def post(self, request, pk):
        service = OTPService()
        try:
            success = service.disconnect_bot()
            if success:
                messages.success(request, "Bot disconnected successfully.")
            else:
                messages.warning(request, "Bot was not connected or disconnect failed.")
        except Exception as e:
            logger.exception("[OTP Admin] Disconnect failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_manage_url())


class OTPBotRefreshStatusView(OTPBotManageBaseView):
    """Refresh bot status from WAHA (just redirects to manage page which syncs)."""

    def post(self, request, pk):
        messages.info(request, "Status refreshed.")
        return HttpResponseRedirect(self.get_manage_url())
