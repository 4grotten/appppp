"""
Custom admin views for Telegram Userbot management.
Provides UI for authentication, testing, and debugging.
"""
import json
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from messenger_bots.models import TelegramUserbot, UserbotAuthState
from messenger_bots.services.bot_factory import UserbotAuthService
from messenger_bots.forms import (
    SendCodeForm,
    VerifyCodeForm,
    Verify2FAForm,
    TestMessageForm,
)


class UserbotAuthBaseView(View):
    """Base view for userbot authentication."""

    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.userbot = get_object_or_404(TelegramUserbot, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_admin_url(self):
        """Get URL to admin change page."""
        return reverse(
            "admin:messenger_bots_telegramuserbot_change",
            args=[self.userbot.pk]
        )

    def get_context(self, **extra):
        """Get base context for templates."""
        context = {
            "userbot": self.userbot,
            "title": f"Userbot: {self.userbot.phone_number}",
            "opts": TelegramUserbot._meta,
            "site_header": admin.site.site_header,
            "site_title": admin.site.site_title,
            "has_view_permission": True,
            **extra,
        }
        return context


class UserbotSendCodeView(UserbotAuthBaseView):
    """View to send verification code."""
    template_name = "admin/messenger_bots/telegramuserbot/send_code.html"

    def get(self, request, pk):
        form = SendCodeForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        form = SendCodeForm(request.POST)
        if form.is_valid():
            service = UserbotAuthService(self.userbot)
            result = UserbotAuthService.run_async(service.send_code())

            if result.get("success"):
                if result.get("already_authenticated"):
                    messages.success(request, "Already authenticated!")
                else:
                    messages.success(
                        request,
                        f"Code sent to {self.userbot.phone_number}. "
                        "Please enter the verification code."
                    )
                    return HttpResponseRedirect(
                        reverse(
                            "admin:messenger_bots_userbot_verify_code",
                            args=[self.userbot.pk]
                        )
                    )
            else:
                messages.error(request, f"Error: {result.get('error')}")

            return HttpResponseRedirect(self.get_admin_url())

        return render(request, self.template_name, self.get_context(form=form))


class UserbotVerifyCodeView(UserbotAuthBaseView):
    """View to verify phone code."""
    template_name = "admin/messenger_bots/telegramuserbot/verify_code.html"

    def get(self, request, pk):
        if self.userbot.auth_state not in [
            UserbotAuthState.CODE_SENT,
            UserbotAuthState.ERROR,
        ]:
            messages.warning(
                request,
                "Please send verification code first."
            )
            return HttpResponseRedirect(
                reverse(
                    "admin:messenger_bots_userbot_send_code",
                    args=[self.userbot.pk]
                )
            )

        form = VerifyCodeForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            service = UserbotAuthService(self.userbot)
            result = UserbotAuthService.run_async(service.verify_code(code))

            if result.get("success"):
                user_info = result.get("user_info", {})
                messages.success(
                    request,
                    f"Successfully authenticated as {user_info.get('first_name', 'User')}!"
                )
                return HttpResponseRedirect(self.get_admin_url())
            elif result.get("needs_2fa"):
                messages.info(
                    request,
                    "2FA is enabled. Please enter your password."
                )
                return HttpResponseRedirect(
                    reverse(
                        "admin:messenger_bots_userbot_verify_2fa",
                        args=[self.userbot.pk]
                    )
                )
            else:
                messages.error(request, f"Error: {result.get('error')}")

        return render(request, self.template_name, self.get_context(form=form))


class UserbotVerify2FAView(UserbotAuthBaseView):
    """View to verify 2FA password."""
    template_name = "admin/messenger_bots/telegramuserbot/verify_2fa.html"

    def get(self, request, pk):
        if self.userbot.auth_state != UserbotAuthState.AWAITING_2FA:
            messages.warning(
                request,
                "2FA verification not required at this stage."
            )
            return HttpResponseRedirect(self.get_admin_url())

        form = Verify2FAForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        form = Verify2FAForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            service = UserbotAuthService(self.userbot)
            result = UserbotAuthService.run_async(service.verify_2fa(password))

            if result.get("success"):
                user_info = result.get("user_info", {})
                messages.success(
                    request,
                    f"Successfully authenticated with 2FA as {user_info.get('first_name', 'User')}!"
                )
            else:
                messages.error(request, f"Error: {result.get('error')}")

            return HttpResponseRedirect(self.get_admin_url())

        return render(request, self.template_name, self.get_context(form=form))


class UserbotCheckConnectionView(UserbotAuthBaseView):
    """View to check connection status."""
    template_name = "admin/messenger_bots/telegramuserbot/check_connection.html"

    def get(self, request, pk):
        service = UserbotAuthService(self.userbot)
        result = UserbotAuthService.run_async(service.check_connection())

        context = self.get_context(
            result=result,
            result_json=json.dumps(result, indent=2, default=str),
        )
        return render(request, self.template_name, context)


class UserbotLogoutView(UserbotAuthBaseView):
    """View to logout userbot."""

    def get(self, request, pk):
        return render(
            request,
            "admin/messenger_bots/telegramuserbot/logout_confirm.html",
            self.get_context()
        )

    def post(self, request, pk):
        service = UserbotAuthService(self.userbot)
        result = UserbotAuthService.run_async(service.logout())

        if result.get("success"):
            messages.success(request, result.get("message"))
        else:
            messages.error(request, f"Error: {result.get('error')}")

        return HttpResponseRedirect(self.get_admin_url())


class UserbotDialogsView(UserbotAuthBaseView):
    """View to see userbot dialogs."""
    template_name = "admin/messenger_bots/telegramuserbot/dialogs.html"

    def get(self, request, pk):
        if not self.userbot.is_authenticated:
            messages.error(request, "Userbot is not authenticated.")
            return HttpResponseRedirect(self.get_admin_url())

        service = UserbotAuthService(self.userbot)
        result = UserbotAuthService.run_async(service.get_dialogs(limit=30))

        context = self.get_context(
            result=result,
            dialogs=result.get("dialogs", []),
        )
        return render(request, self.template_name, context)


class UserbotTestMessageView(UserbotAuthBaseView):
    """View to send a test message."""
    template_name = "admin/messenger_bots/telegramuserbot/test_message.html"

    def get(self, request, pk):
        if not self.userbot.is_authenticated:
            messages.error(request, "Userbot is not authenticated.")
            return HttpResponseRedirect(self.get_admin_url())

        form = TestMessageForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        if not self.userbot.is_authenticated:
            messages.error(request, "Userbot is not authenticated.")
            return HttpResponseRedirect(self.get_admin_url())

        form = TestMessageForm(request.POST)
        if form.is_valid():
            chat = form.cleaned_data["chat"]
            message = form.cleaned_data["message"]

            service = UserbotAuthService(self.userbot)
            result = UserbotAuthService.run_async(
                service.send_test_message(chat, message)
            )

            if result.get("success"):
                messages.success(request, f"Message sent to {chat}!")
            else:
                messages.error(request, f"Error: {result.get('error')}")

            return HttpResponseRedirect(self.get_admin_url())

        return render(request, self.template_name, self.get_context(form=form))
