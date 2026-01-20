# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger_bots', '0007_telegrambot_context_messages_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botchat',
            name='user_phone',
            field=models.CharField(
                blank=True,
                help_text='User\'s phone number or chat ID (for WhatsApp)',
                max_length=50,
                null=True,
            ),
        ),
    ]
