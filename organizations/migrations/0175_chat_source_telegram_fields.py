# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("messenger_bots", "0007_telegrambot_context_messages_limit"),
        ("organizations", "0174_auto_20260109_1430"),
    ]

    operations = [
        # Add source field
        migrations.AddField(
            model_name="chat",
            name="source",
            field=models.CharField(
                choices=[("web", "Web"), ("telegram", "Telegram"), ("whatsapp", "WhatsApp")],
                default="web",
                max_length=20,
            ),
        ),
        # Add bot_chat field
        migrations.AddField(
            model_name="chat",
            name="bot_chat",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="linked_chat",
                to="messenger_bots.botchat",
            ),
        ),
        # Add unread_count field
        migrations.AddField(
            model_name="chat",
            name="unread_count",
            field=models.PositiveIntegerField(default=0),
        ),
        # Add is_read field
        migrations.AddField(
            model_name="chat",
            name="is_read",
            field=models.BooleanField(default=True),
        ),
        # Make user nullable
        migrations.AlterField(
            model_name="chat",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chats",
                to="users.user",
            ),
        ),
        # Remove old constraint
        migrations.RemoveConstraint(
            model_name="chat",
            name="one_chat_between_user_and_assistant",
        ),
        # Add new constraints with conditions
        migrations.AddConstraint(
            model_name="chat",
            constraint=models.UniqueConstraint(
                condition=models.Q(source="web"),
                fields=("user", "assistant"),
                name="one_chat_between_user_and_assistant",
            ),
        ),
        migrations.AddConstraint(
            model_name="chat",
            constraint=models.UniqueConstraint(
                condition=models.Q(bot_chat__isnull=False),
                fields=("bot_chat",),
                name="one_chat_per_bot_chat",
            ),
        ),
    ]
