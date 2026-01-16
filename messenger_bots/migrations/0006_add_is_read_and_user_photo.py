# Generated manually on 2026-01-15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger_bots', '0005_botcreationrequest_base_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='botchat',
            name='user_photo',
            field=models.URLField(blank=True, help_text="User's profile photo URL from the platform", max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='botmessage',
            name='is_read',
            field=models.BooleanField(default=False, help_text='Whether the message has been read by admin'),
        ),
    ]
