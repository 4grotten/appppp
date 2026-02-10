from django.apps import AppConfig


class OtpBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "otp_bot"
    verbose_name = "OTP Bot (WhatsApp)"

    def ready(self):
        """Register signals when app is ready."""
        import otp_bot.signals  # noqa: F401
