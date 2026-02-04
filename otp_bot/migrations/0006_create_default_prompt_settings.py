# Data migration to create default OTPBotPromptSettings instance

from django.db import migrations


def create_default_settings(apps, schema_editor):
    """Create singleton instance with default escalation keywords."""
    OTPBotPromptSettings = apps.get_model("otp_bot", "OTPBotPromptSettings")

    # Only create if not exists
    if not OTPBotPromptSettings.objects.exists():
        OTPBotPromptSettings.objects.create(
            is_active=True,
            escalation_keywords=["оператор", "человек", "помощь", "живой", "operator", "human", "help"],
        )


def remove_default_settings(apps, schema_editor):
    """Remove singleton instance on rollback."""
    OTPBotPromptSettings = apps.get_model("otp_bot", "OTPBotPromptSettings")
    OTPBotPromptSettings.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("otp_bot", "0005_otpbotpromptsettings"),
    ]

    operations = [
        migrations.RunPython(create_default_settings, remove_default_settings),
    ]
