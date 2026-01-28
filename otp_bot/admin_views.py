"""Custom admin views for OTP Bot management (per-object, like TelegramUserbot)."""

import logging

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from otp_bot.models import OTPBot
from otp_bot.services.otp_service import OTPService
from otp_bot.services.waha_otp import WAHAOTPClient

logger = logging.getLogger(__name__)


class OTPBotBaseView(View):
    """Base view for OTP bot admin actions."""

    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.bot = get_object_or_404(OTPBot, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_change_url(self) -> str:
        return reverse("admin:otp_bot_otpbot_change", args=[self.bot.pk])

    def get_context(self, **extra) -> dict:
        return {
            "bot": self.bot,
            "title": f"OTP Bot: {self.bot.waha_session_name}",
            "opts": OTPBot._meta,
            "site_header": admin.site.site_header or "Django administration",
            "site_title": admin.site.site_title or "Django site admin",
            "has_view_permission": True,
            **extra,
        }


class OTPBotStartSessionView(OTPBotBaseView):
    """Start WAHA session for OTP bot."""

    def get(self, request, pk):
        """Start session and redirect to QR page."""
        service = OTPService(waha_client=WAHAOTPClient(session_name=self.bot.waha_session_name))
        try:
            success = service.waha.start_session()
            if success:
                self.bot.status = "qr_pending"
                self.bot.save(update_fields=["status", "updated_at"])
                messages.success(request, "Session started. Scan the QR code.")
                return HttpResponseRedirect(
                    reverse("admin:otp_bot_otpbot_qr", args=[self.bot.pk])
                )
            else:
                self.bot.status = "failed"
                self.bot.save(update_fields=["status", "updated_at"])
                messages.error(request, "Failed to start WAHA session.")
        except Exception as e:
            logger.exception("[OTP Admin] Start session failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_change_url())


class OTPBotQRCodeView(OTPBotBaseView):
    """Show QR code page with auto-refresh."""

    template_name = "admin/otp_bot/qr_code.html"

    def get(self, request, pk):
        service = OTPService(waha_client=WAHAOTPClient(session_name=self.bot.waha_session_name))

        # Sync status from WAHA first
        bot = service.get_bot_status()
        if bot:
            self.bot = bot

        # If already connected, redirect back to change form
        if self.bot.status == "connected":
            messages.success(request, "Bot is connected!")
            return HttpResponseRedirect(self.get_change_url())

        # Get QR code
        qr_code = None
        if self.bot.status == "qr_pending":
            qr_code = service.get_qr_code()

        return render(request, self.template_name, self.get_context(qr_code=qr_code))

    def post(self, request, pk):
        """Check if QR was scanned (refresh status)."""
        service = OTPService(waha_client=WAHAOTPClient(session_name=self.bot.waha_session_name))
        bot = service.get_bot_status()
        if bot:
            self.bot = bot

        if self.bot.status == "connected":
            messages.success(request, "Bot connected successfully!")
            return HttpResponseRedirect(self.get_change_url())

        messages.info(request, "Still waiting for QR scan...")
        return HttpResponseRedirect(
            reverse("admin:otp_bot_otpbot_qr", args=[self.bot.pk])
        )


class OTPBotDisconnectView(OTPBotBaseView):
    """Disconnect OTP bot session."""

    def get(self, request, pk):
        """Disconnect and redirect back to change form."""
        service = OTPService(waha_client=WAHAOTPClient(session_name=self.bot.waha_session_name))
        try:
            service.disconnect_bot()
            messages.success(request, "Bot disconnected.")
        except Exception as e:
            logger.exception("[OTP Admin] Disconnect failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_change_url())


class OTPBotStopSessionView(OTPBotBaseView):
    """Stop WAHA session (keeps session data, can restart)."""

    def get(self, request, pk):
        waha = WAHAOTPClient(session_name=self.bot.waha_session_name)
        try:
            if waha.stop_session():
                self.bot.status = "disconnected"
                self.bot.save(update_fields=["status", "updated_at"])
                messages.success(request, "Session stopped.")
            else:
                messages.error(request, "Failed to stop session.")
        except Exception as e:
            logger.exception("[OTP Admin] Stop session failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_change_url())


class OTPBotLogoutView(OTPBotBaseView):
    """Logout from WhatsApp (requires QR re-scan to reconnect)."""

    def get(self, request, pk):
        waha = WAHAOTPClient(session_name=self.bot.waha_session_name)
        try:
            if waha.logout_session():
                self.bot.status = "disconnected"
                self.bot.phone_number = None
                self.bot.save(update_fields=["status", "phone_number", "updated_at"])
                messages.success(request, "Logged out from WhatsApp. QR scan required to reconnect.")
            else:
                messages.error(request, "Failed to logout.")
        except Exception as e:
            logger.exception("[OTP Admin] Logout failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_change_url())


class OTPBotDeleteSessionView(OTPBotBaseView):
    """Delete session completely (removes all WAHA session data)."""

    def get(self, request, pk):
        waha = WAHAOTPClient(session_name=self.bot.waha_session_name)
        try:
            if waha.delete_session():
                self.bot.status = "disconnected"
                self.bot.phone_number = None
                self.bot.save(update_fields=["status", "phone_number", "updated_at"])
                messages.success(request, "Session deleted completely.")
            else:
                messages.error(request, "Failed to delete session.")
        except Exception as e:
            logger.exception("[OTP Admin] Delete session failed")
            messages.error(request, f"Error: {e}")

        return HttpResponseRedirect(self.get_change_url())


class OTPBotRebindView(OTPBotBaseView):
    """Rebind session: logout + delete + start new session for QR scan."""

    def get(self, request, pk):
        waha = WAHAOTPClient(session_name=self.bot.waha_session_name)
        try:
            # Step 1: Logout (if connected)
            if self.bot.status == "connected":
                waha.logout_session()
                logger.info(f"[OTP Admin] Rebind: logged out session {self.bot.waha_session_name}")

            # Step 2: Delete session data
            waha.delete_session()
            logger.info(f"[OTP Admin] Rebind: deleted session {self.bot.waha_session_name}")

            # Step 3: Start fresh session
            if waha.start_session():
                self.bot.status = "qr_pending"
                self.bot.phone_number = None
                self.bot.save(update_fields=["status", "phone_number", "updated_at"])
                messages.success(request, "Session reset. Scan the QR code to connect new number.")
                return HttpResponseRedirect(
                    reverse("admin:otp_bot_otpbot_qr", args=[self.bot.pk])
                )
            else:
                self.bot.status = "failed"
                self.bot.phone_number = None
                self.bot.save(update_fields=["status", "phone_number", "updated_at"])
                messages.error(request, "Failed to start new session after rebind.")

        except Exception as e:
            logger.exception("[OTP Admin] Rebind failed")
            messages.error(request, f"Rebind error: {e}")

        return HttpResponseRedirect(self.get_change_url())
