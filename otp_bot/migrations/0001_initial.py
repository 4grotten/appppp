# Generated manually

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OTPBot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("waha_session_name", models.CharField(default="otp_service_bot", help_text="WAHA session name for OTP bot", max_length=100)),
                ("phone_number", models.CharField(blank=True, help_text="Connected WhatsApp phone number", max_length=20, null=True)),
                ("status", models.CharField(choices=[("disconnected", "Disconnected"), ("qr_pending", "Waiting for QR scan"), ("connected", "Connected"), ("failed", "Failed")], default="disconnected", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "OTP Bot",
                "verbose_name_plural": "OTP Bots",
            },
        ),
        migrations.CreateModel(
            name="OTPCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("phone_number", models.CharField(db_index=True, help_text="Recipient phone number (E.164)", max_length=20)),
                ("code_hash", models.CharField(help_text="Bcrypt hash of the OTP code", max_length=128)),
                ("expires_at", models.DateTimeField(db_index=True, help_text="When this OTP expires")),
                ("attempts_count", models.PositiveSmallIntegerField(default=0, help_text="Number of verification attempts")),
                ("is_used", models.BooleanField(default=False, help_text="Whether code was successfully verified")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "OTP Code",
                "verbose_name_plural": "OTP Codes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="otpcode",
            index=models.Index(fields=["phone_number", "created_at"], name="idx_otp_phone_created"),
        ),
    ]
