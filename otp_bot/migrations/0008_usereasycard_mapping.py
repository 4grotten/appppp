# Generated manually on 2026-02-04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    """Add UserEasyCardMapping model for user synchronization."""

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("otp_bot", "0007_add_otp_message_templates"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserEasyCardMapping",
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
                    "easycard_user_id",
                    models.UUIDField(
                        db_index=True,
                        help_text="EasyCard Profile user_id (UUID from Supabase)",
                        unique=True,
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        db_index=True,
                        help_text="Shared phone number for linking (E.164)",
                        max_length=20,
                    ),
                ),
                (
                    "synced_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Last sync timestamp",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "apofiz_user",
                    models.OneToOneField(
                        help_text="Apofiz user account",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="easycard_mapping",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "User EasyCard Mapping",
                "verbose_name_plural": "User EasyCard Mappings",
                "indexes": [
                    models.Index(fields=["phone_number"], name="idx_mapping_phone"),
                ],
            },
        ),
    ]
