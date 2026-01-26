"""Update ChatSession index name."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("otp_bot", "0003_chatsession_uservoicepreference"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="chatsession",
            name="otp_bot_cha_phone_n_abc123_idx",
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(
                fields=["phone_number", "-updated_at"],
                name="otp_bot_cha_phone_n_d28539_idx",
            ),
        ),
    ]
