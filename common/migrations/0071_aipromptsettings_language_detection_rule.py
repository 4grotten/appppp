# Generated manually on 2026-01-19
# Add language_detection_rule field to AIPromptSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0070_aipromptsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='aipromptsettings',
            name='language_detection_rule',
            field=models.TextField(
                default=(
                    "🌐 CRITICAL LANGUAGE RULE:\n"
                    "Detect the language from USER'S MESSAGES (not from any settings).\n"
                    "- If user writes in English (Hello, What can you do, etc.) → respond in ENGLISH\n"
                    "- If user writes in Russian (Привет, Что умеешь, etc.) → respond in RUSSIAN\n"
                    "- If user explicitly asks 'Speak English' or 'Говори по-русски' → switch to that language\n"
                    "- Translate all data (products, contacts) to the user's language."
                ),
                verbose_name='Language Detection Rule',
                help_text='Правило определения языка из контекста сообщений'
            ),
        ),
    ]
