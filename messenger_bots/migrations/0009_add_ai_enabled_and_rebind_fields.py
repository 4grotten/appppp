# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger_bots', '0008_increase_user_phone_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegrambot',
            name='is_ai_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Whether AI assistant responds to messages. If False, bot receives messages but stays silent.',
            ),
        ),
        migrations.AddField(
            model_name='whatsappbot',
            name='is_ai_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Whether AI assistant responds to messages. If False, bot receives messages but stays silent.',
            ),
        ),
        migrations.AddField(
            model_name='whatsappbot',
            name='previous_phone_number',
            field=models.CharField(
                blank=True,
                help_text='Previous phone number before rebind',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='whatsappbot',
            name='phone_changed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp when phone number was changed (rebind)',
                null=True,
            ),
        ),
    ]
