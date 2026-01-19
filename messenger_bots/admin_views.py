import json
import logging

from celery.exceptions import TimeoutError as CeleryTimeoutError
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from messenger_bots.forms import (
    SendCodeForm,
    TestMessageForm,
    Verify2FAForm,
    VerifyCodeForm,
)
from messenger_bots.models import TelegramUserbot, UserbotAuthState
from messenger_bots.tasks import (
    userbot_check_connection_task,
    userbot_get_dialogs_task,
    userbot_logout_task,
    userbot_qr_login_check_task,
    userbot_qr_login_start_task,
    userbot_send_code_task,
    userbot_send_test_message_task,
    userbot_verify_2fa_task,
    userbot_verify_code_task,
)

logger = logging.getLogger(__name__)

CELERY_TASK_TIMEOUT = 90


class UserbotAuthBaseView(View):

    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.userbot = get_object_or_404(TelegramUserbot, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_admin_url(self):
        return reverse(
            "admin:messenger_bots_telegramuserbot_change", args=[self.userbot.pk]
        )

    def get_context(self, **extra):
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
    template_name = "admin/messenger_bots/telegramuserbot/send_code.html"

    def get(self, request, pk):
        form = SendCodeForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        form = SendCodeForm(request.POST)
        if form.is_valid():
            try:
                task = userbot_send_code_task.delay(self.userbot.pk)
                result = task.get(timeout=CELERY_TASK_TIMEOUT)

                if result.get("success"):
                    if result.get("already_authenticated"):
                        messages.success(request, "Already authenticated!")
                    else:
                        messages.success(
                            request,
                            f"Code sent to {self.userbot.phone_number}. "
                            "Please enter the verification code.",
                        )
                        return HttpResponseRedirect(
                            reverse(
                                "admin:messenger_bots_userbot_verify_code",
                                args=[self.userbot.pk],
                            )
                        )
                else:
                    messages.error(request, f"Error: {result.get('error')}")

            except CeleryTimeoutError:
                logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
                messages.error(request, "Operation timed out. Please try again.")
            except Exception as e:
                logger.error(f"Celery task error: {e}", exc_info=True)
                messages.error(request, f"Error: {str(e)}")

            return HttpResponseRedirect(self.get_admin_url())

        return render(request, self.template_name, self.get_context(form=form))


class UserbotVerifyCodeView(UserbotAuthBaseView):
    template_name = "admin/messenger_bots/telegramuserbot/verify_code.html"

    def get(self, request, pk):
        if self.userbot.auth_state not in [
            UserbotAuthState.CODE_SENT,
            UserbotAuthState.ERROR,
        ]:
            messages.warning(request, "Please send verification code first.")
            return HttpResponseRedirect(
                reverse(
                    "admin:messenger_bots_userbot_send_code", args=[self.userbot.pk]
                )
            )

        form = VerifyCodeForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]

            try:
                task = userbot_verify_code_task.delay(self.userbot.pk, code)
                result = task.get(timeout=CELERY_TASK_TIMEOUT)

                if result.get("success"):
                    user_info = result.get("user_info", {})
                    messages.success(
                        request,
                        f"Successfully authenticated as {user_info.get('first_name', 'User')}!",
                    )
                    return HttpResponseRedirect(self.get_admin_url())
                elif result.get("needs_2fa"):
                    messages.info(
                        request, "2FA is enabled. Please enter your password."
                    )
                    return HttpResponseRedirect(
                        reverse(
                            "admin:messenger_bots_userbot_verify_2fa",
                            args=[self.userbot.pk],
                        )
                    )
                else:
                    messages.error(request, f"Error: {result.get('error')}")

            except CeleryTimeoutError:
                logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
                messages.error(request, "Operation timed out. Please try again.")
            except Exception as e:
                logger.error(f"Celery task error: {e}", exc_info=True)
                messages.error(request, f"Error: {str(e)}")

        return render(request, self.template_name, self.get_context(form=form))


class UserbotQRLoginView(UserbotAuthBaseView):
    """QR code login - generates QR and waits for scan."""
    template_name = "admin/messenger_bots/telegramuserbot/qr_login.html"

    # Datacenter options for region selection
    DC_CHOICES = [
        (None, "Auto (let Telegram decide)"),
        (2, "🇪🇺 Europe / CIS (DC2 - Netherlands)"),
        (5, "🌏 Asia / UAE / Middle East (DC5 - Singapore)"),
        (3, "🇺🇸 USA (DC3 - Miami)"),
        (1, "🧪 Test (DC1)"),
    ]

    def get(self, request, pk):
        # Check if we're generating QR or showing region selection
        force_dc = request.GET.get("dc")

        if force_dc is None and "generate" not in request.GET:
            # Show region selection form first
            return render(
                request,
                self.template_name,
                self.get_context(
                    show_region_select=True,
                    dc_choices=self.DC_CHOICES,
                ),
            )

        # Parse force_dc parameter
        force_dc_int = None
        if force_dc and force_dc.isdigit():
            force_dc_int = int(force_dc)

        # Start QR login process with optional forced datacenter
        try:
            task = userbot_qr_login_start_task.delay(self.userbot.pk, force_dc=force_dc_int)
            result = task.get(timeout=CELERY_TASK_TIMEOUT)

            if result.get("success"):
                if result.get("already_authenticated"):
                    messages.success(request, "Already authenticated!")
                    return HttpResponseRedirect(self.get_admin_url())

                # Generate QR code image
                qr_url = result.get("qr_url")
                qr_image_base64 = self._generate_qr_image(qr_url)
                datacenter = result.get("datacenter", "unknown")

                return render(
                    request,
                    self.template_name,
                    self.get_context(
                        qr_url=qr_url,
                        qr_image=qr_image_base64,
                        expires=result.get("expires"),
                        datacenter=datacenter,
                        dc_choices=self.DC_CHOICES,
                    ),
                )
            else:
                error_msg = result.get("error", "Unknown error")
                messages.error(request, f"Error: {error_msg}")

                # If it's a datacenter error, suggest trying different region
                if "migration" in error_msg.lower() or "datacenter" in error_msg.lower():
                    messages.info(
                        request,
                        "Try selecting a different region (e.g., Asia/UAE for Middle East users)."
                    )

                return HttpResponseRedirect(self.get_admin_url())

        except CeleryTimeoutError:
            logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
            messages.error(request, "Operation timed out. Please try again.")
            return HttpResponseRedirect(self.get_admin_url())
        except Exception as e:
            logger.error(f"Celery task error: {e}", exc_info=True)
            messages.error(request, f"Error: {str(e)}")
            return HttpResponseRedirect(self.get_admin_url())

    def post(self, request, pk):
        """Check if QR was scanned."""
        try:
            task = userbot_qr_login_check_task.delay(self.userbot.pk)
            result = task.get(timeout=CELERY_TASK_TIMEOUT)

            if result.get("success"):
                user_info = result.get("user_info", {})
                messages.success(
                    request,
                    f"Successfully authenticated as {user_info.get('first_name', 'User')}!",
                )
                return HttpResponseRedirect(self.get_admin_url())
            elif result.get("needs_2fa"):
                messages.info(
                    request, "2FA is enabled. Please enter your password."
                )
                return HttpResponseRedirect(
                    reverse(
                        "admin:messenger_bots_userbot_verify_2fa",
                        args=[self.userbot.pk],
                    )
                )
            elif result.get("not_scanned"):
                messages.warning(
                    request, "QR code not scanned yet. Please scan and try again."
                )
            else:
                messages.error(request, f"Error: {result.get('error')}")

        except CeleryTimeoutError:
            logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
            messages.error(request, "Operation timed out. Please try again.")
        except Exception as e:
            logger.error(f"Celery task error: {e}", exc_info=True)
            messages.error(request, f"Error: {str(e)}")

        return HttpResponseRedirect(
            reverse("admin:messenger_bots_userbot_qr_login", args=[self.userbot.pk])
        )

    def _generate_qr_image(self, url: str) -> str:
        """Generate QR code image as base64 string."""
        import base64
        import io

        try:
            import qrcode
            from qrcode.image.pure import PyPNGImage

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(image_factory=PyPNGImage)
            buffer = io.BytesIO()
            img.save(buffer)
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")
        except ImportError:
            logger.warning("qrcode library not installed, QR image not generated")
            return ""


class UserbotVerify2FAView(UserbotAuthBaseView):
    template_name = "admin/messenger_bots/telegramuserbot/verify_2fa.html"

    def get(self, request, pk):
        if self.userbot.auth_state != UserbotAuthState.AWAITING_2FA:
            messages.warning(request, "2FA verification not required at this stage.")
            return HttpResponseRedirect(self.get_admin_url())

        form = Verify2FAForm()
        return render(request, self.template_name, self.get_context(form=form))

    def post(self, request, pk):
        form = Verify2FAForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]

            try:
                task = userbot_verify_2fa_task.delay(self.userbot.pk, password)
                result = task.get(timeout=CELERY_TASK_TIMEOUT)

                if result.get("success"):
                    user_info = result.get("user_info", {})
                    messages.success(
                        request,
                        f"Successfully authenticated with 2FA as {user_info.get('first_name', 'User')}!",
                    )
                else:
                    messages.error(request, f"Error: {result.get('error')}")

            except CeleryTimeoutError:
                logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
                messages.error(request, "Operation timed out. Please try again.")
            except Exception as e:
                logger.error(f"Celery task error: {e}", exc_info=True)
                messages.error(request, f"Error: {str(e)}")

            return HttpResponseRedirect(self.get_admin_url())

        return render(request, self.template_name, self.get_context(form=form))


class UserbotCheckConnectionView(UserbotAuthBaseView):
    template_name = "admin/messenger_bots/telegramuserbot/check_connection.html"

    def get(self, request, pk):
        try:
            task = userbot_check_connection_task.delay(self.userbot.pk)
            result = task.get(timeout=CELERY_TASK_TIMEOUT)
        except CeleryTimeoutError:
            result = {"success": False, "error": "Operation timed out"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

        context = self.get_context(
            result=result,
            result_json=json.dumps(result, indent=2, default=str),
        )
        return render(request, self.template_name, context)


class UserbotLogoutView(UserbotAuthBaseView):

    def get(self, request, pk):
        return render(
            request,
            "admin/messenger_bots/telegramuserbot/logout_confirm.html",
            self.get_context(),
        )

    def post(self, request, pk):
        try:
            task = userbot_logout_task.delay(self.userbot.pk)
            result = task.get(timeout=CELERY_TASK_TIMEOUT)

            if result.get("success"):
                messages.success(request, result.get("message"))
            else:
                messages.error(request, f"Error: {result.get('error')}")

        except CeleryTimeoutError:
            logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
            messages.error(request, "Operation timed out. Please try again.")
        except Exception as e:
            logger.error(f"Celery task error: {e}", exc_info=True)
            messages.error(request, f"Error: {str(e)}")

        return HttpResponseRedirect(self.get_admin_url())


class UserbotDialogsView(UserbotAuthBaseView):
    template_name = "admin/messenger_bots/telegramuserbot/dialogs.html"

    def get(self, request, pk):
        if not self.userbot.is_authenticated:
            messages.error(request, "Userbot is not authenticated.")
            return HttpResponseRedirect(self.get_admin_url())

        try:
            task = userbot_get_dialogs_task.delay(self.userbot.pk, limit=30)
            result = task.get(timeout=CELERY_TASK_TIMEOUT)
        except CeleryTimeoutError:
            result = {"success": False, "error": "Operation timed out", "dialogs": []}
        except Exception as e:
            result = {"success": False, "error": str(e), "dialogs": []}

        context = self.get_context(
            result=result,
            dialogs=result.get("dialogs", []),
        )
        return render(request, self.template_name, context)


class UserbotTestMessageView(UserbotAuthBaseView):
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

            try:
                task = userbot_send_test_message_task.delay(
                    self.userbot.pk, chat, message
                )
                result = task.get(timeout=CELERY_TASK_TIMEOUT)

                if result.get("success"):
                    messages.success(request, f"Message sent to {chat}!")
                else:
                    messages.error(request, f"Error: {result.get('error')}")

            except CeleryTimeoutError:
                logger.error(f"Celery task timeout for userbot {self.userbot.pk}")
                messages.error(request, "Operation timed out. Please try again.")
            except Exception as e:
                logger.error(f"Celery task error: {e}", exc_info=True)
                messages.error(request, f"Error: {str(e)}")

            return HttpResponseRedirect(self.get_admin_url())

        return render(request, self.template_name, self.get_context(form=form))
