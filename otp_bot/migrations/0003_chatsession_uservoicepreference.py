"""Add ChatSession and UserVoicePreference models for Finance AI Voice Assistant.

ChatSession stores conversation history for AI context.
UserVoicePreference controls voice response mode per user.
"""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("otp_bot", "0002_alter_otpbot_waha_session_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        db_index=True,
                        help_text="User phone number (E.164)",
                        max_length=20,
                        unique=True,
                    ),
                ),
                (
                    "messages",
                    models.JSONField(
                        default=list,
                        help_text="Chat history: [{role, content}, ...]",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Chat Session",
                "verbose_name_plural": "Chat Sessions",
            },
        ),
        migrations.CreateModel(
            name="UserVoicePreference",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        db_index=True,
                        help_text="User phone number (E.164)",
                        max_length=20,
                        unique=True,
                    ),
                ),
                (
                    "voice_enabled",
                    models.BooleanField(
                        default=False,
                        help_text="If True, always respond with voice. If False, match input type.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "User Voice Preference",
                "verbose_name_plural": "User Voice Preferences",
            },
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(
                fields=["phone_number", "-updated_at"],
                name="otp_bot_cha_phone_n_abc123_idx",
            ),
        ),
    ]
