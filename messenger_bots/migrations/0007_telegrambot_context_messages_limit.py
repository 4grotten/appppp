# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messenger_bots", "0006_add_is_read_and_user_photo"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegrambot",
            name="context_messages_limit",
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text=(
                    "Number of message pairs (user+assistant) to include in AI context. "
                    "Default: 5 pairs = 10 messages. Range: 1-20."
                ),
            ),
        ),
    ]
