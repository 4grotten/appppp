"""Change OTPBot waha_session_name default from 'otp_service_bot' to 'default'.

WAHA Core only supports 'default' session name.
"""

from django.db import migrations, models


def fix_session_names(apps, schema_editor):
    OTPBot = apps.get_model("otp_bot", "OTPBot")
    OTPBot.objects.filter(waha_session_name="otp_service_bot").update(
        waha_session_name="default"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("otp_bot", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otpbot",
            name="waha_session_name",
            field=models.CharField(
                default="default",
                help_text="WAHA session name for OTP bot",
                max_length=100,
            ),
        ),
        migrations.RunPython(fix_session_names, migrations.RunPython.noop),
    ]
