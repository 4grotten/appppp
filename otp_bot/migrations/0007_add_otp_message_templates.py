# Generated manually for OTP message template fields

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("otp_bot", "0006_create_default_prompt_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="otpbotpromptsettings",
            name="otp_message_new_user",
            field=models.TextField(
                default=(
                    "Здравствуйте! 👋\n\n"
                    "Я ваш личный ассистент Easy Card 💳\n"
                    "Помогу вам пройти регистрацию и отвечу на любые вопросы о картах, "
                    "комиссиях и переводах.\n\n"
                    "Ваш код подтверждения: {code}\n\n"
                    "⏱ Код действителен {ttl_minutes} мин.\n"
                    "🔒 Не сообщайте его никому."
                ),
                verbose_name="OTP Message (New User)",
                help_text="Message sent with OTP code for first-time users. Use {code} and {ttl_minutes} placeholders.",
            ),
        ),
        migrations.AddField(
            model_name="otpbotpromptsettings",
            name="otp_message_existing_user",
            field=models.TextField(
                default=(
                    "Ваш код подтверждения: {code}\n\n"
                    "Код действителен {ttl_minutes} мин. Не сообщайте его никому."
                ),
                verbose_name="OTP Message (Existing User)",
                help_text="Message sent with OTP code for returning users. Use {code} and {ttl_minutes} placeholders.",
            ),
        ),
        migrations.AddField(
            model_name="otpbotpromptsettings",
            name="welcome_message_after_registration",
            field=models.TextField(
                default=(
                    "Отлично! Регистрация успешно завершена 🎉\n\n"
                    "Добро пожаловать в Easy Card!\n\n"
                    "Я всегда на связи и готов помочь:\n"
                    "• Узнать баланс и историю операций\n"
                    "• Рассказать о комиссиях и лимитах\n"
                    "• Ответить на вопросы о картах\n\n"
                    "Просто напишите мне! 💬"
                ),
                verbose_name="Welcome Message After Registration",
                help_text="Message sent after successful OTP verification for new users.",
            ),
        ),
    ]
