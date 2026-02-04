# Generated manually for OTPBotPromptSettings

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("otp_bot", "0004_alter_chatsession_index"),
    ]

    operations = [
        migrations.CreateModel(
            name="OTPBotPromptSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="If disabled, uses default prompts from prompts.py",
                        verbose_name="Active",
                    ),
                ),
                (
                    "system_prompt_core",
                    models.TextField(
                        default="Ты - дружелюбный AI-ассистент для финансового приложения Easy Card.\nОтвечай кратко и по делу на языке пользователя. Используй эмодзи для дружелюбности.",
                        help_text="Main AI identity and behavior instructions",
                        verbose_name="Core System Prompt",
                    ),
                ),
                (
                    "about_easycard",
                    models.TextField(
                        default="Easy Card - это финансовое приложение для управления виртуальными и металлическими картами в ОАЭ (валюта AED - дирхамы).",
                        help_text="General description of EasyCard service",
                        verbose_name="About Easy Card",
                    ),
                ),
                (
                    "card_types",
                    models.TextField(
                        default="1. **Виртуальная карта** - мгновенный выпуск, идеально для онлайн-покупок\n2. **Металлическая карта** - премиум карта с доставкой, статусная и долговечная",
                        help_text="Virtual and Metal card descriptions",
                        verbose_name="Card Types",
                    ),
                ),
                (
                    "fees_one_time",
                    models.TextField(
                        default="- Годовое обслуживание виртуальной карты: 183 AED\n- Перевыпуск виртуальной карты: 183 AED\n- Годовое обслуживание металлической карты: 183 AED\n- Перевыпуск металлической карты: 183 AED\n- Открытие виртуального счета: 183 AED",
                        help_text="Annual service, replacement fees in AED",
                        verbose_name="One-Time Fees",
                    ),
                ),
                (
                    "fees_topup",
                    models.TextField(
                        default="- Криптовалютой (USDT): фиксированная комиссия 5.90 USDT\n- Банковским переводом: 1.5%\n- Минимальная сумма пополнения криптой: 15 USDT\n- Минимальная сумма пополнения банком: 50 AED",
                        help_text="Crypto and bank transfer fees",
                        verbose_name="Top-Up Fees",
                    ),
                ),
                (
                    "fees_transfer",
                    models.TextField(
                        default="- С карты на карту: 1%\n- Банковский перевод: 2%\n- Сетевая комиссия: 1%",
                        help_text="Card-to-card, bank transfer, network fees",
                        verbose_name="Transfer Fees",
                    ),
                ),
                (
                    "fees_transactions",
                    models.TextField(
                        default="- Конвертация валюты: 1.5%",
                        help_text="Currency conversion fees",
                        verbose_name="Transaction Fees",
                    ),
                ),
                (
                    "exchange_rates",
                    models.TextField(
                        default="- Пополнение: 1 USDT = 3.65 AED\n- Вывод: 1 USDT = 3.69 AED",
                        help_text="USDT/AED rates for top-up and withdrawal",
                        verbose_name="Exchange Rates",
                    ),
                ),
                (
                    "app_features",
                    models.TextField(
                        default="- Управление картами (виртуальные и металлические)\n- Пополнение баланса (криптой USDT или банковским переводом)\n- Переводы (на карту, на банк, криптой)\n- История транзакций\n- Настройка лимитов\n- Верификация личности (KYC)\n- Мультиязычность (EN, RU, AR, DE, ES, TR, ZH)",
                        help_text="List of EasyCard app capabilities",
                        verbose_name="App Features",
                    ),
                ),
                (
                    "important_notes",
                    models.TextField(
                        default="- Все карты работают в валюте AED (дирхамы ОАЭ)\n- Для использования карт нужно пройти верификацию\n- Поддерживаются сети TRC20 и ERC20 для крипто-пополнений",
                        help_text="KYC requirements, supported networks, etc.",
                        verbose_name="Important Notes",
                    ),
                ),
                (
                    "scenario_new_user",
                    models.TextField(
                        default="Для новых пользователей (не зарегистрированных в EasyCard):\n- Приветствие с OTP кодом\n- Предложение перейти в чат EasyCard\n- После регистрации - предложение получить карту",
                        help_text="Instructions for users not in EasyCard DB",
                        verbose_name="Scenario: New User",
                    ),
                ),
                (
                    "scenario_existing_user",
                    models.TextField(
                        default="Для существующих пользователей:\n- Отправка OTP кода\n- Консультация по приложению\n- Помощь с переводами и функциями",
                        help_text="Instructions for registered users",
                        verbose_name="Scenario: Existing User",
                    ),
                ),
                (
                    "scenario_consultation",
                    models.TextField(
                        default="При консультации по EasyCard:\n- Отвечай на вопросы о картах, комиссиях, функциях\n- Помогай с навигацией по приложению\n- Если вопрос не про EasyCard - вежливо объясни свою специализацию",
                        help_text="AI consultation behavior instructions",
                        verbose_name="Scenario: Consultation",
                    ),
                ),
                (
                    "scenario_escalation",
                    models.TextField(
                        default="Когда переводить на оператора:\n- Пользователь явно просит связаться с человеком\n- Сложные технические проблемы\n- Жалобы на работу сервиса\n- Вопросы, выходящие за рамки компетенции бота",
                        help_text="When to redirect to human operator",
                        verbose_name="Scenario: Escalation",
                    ),
                ),
                (
                    "escalation_keywords",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text='Keywords triggering escalation, e.g. ["оператор", "человек", "помощь"]',
                        verbose_name="Escalation Keywords",
                    ),
                ),
                (
                    "voice_mode_prompt",
                    models.TextField(
                        default="РЕЖИМ ГОЛОСОВОГО ОТВЕТА:\nВАЖНО: Этот ответ будет озвучен голосом, поэтому:\n- Отвечай ОЧЕНЬ кратко\n- Не используй списки, маркеры, форматирование\n- Не используй эмодзи\n- Говори естественно, как по телефону\n- Если нужна детальная информация - предложи написать текстом",
                        help_text="Additional instructions for voice responses",
                        verbose_name="Voice Mode Instructions",
                    ),
                ),
                (
                    "voice_max_words",
                    models.PositiveIntegerField(
                        default=50,
                        help_text="Maximum words for voice responses",
                        verbose_name="Voice Max Words",
                    ),
                ),
                (
                    "language_detection_rule",
                    models.TextField(
                        default="Правила определения языка:\n1. Определяй язык из сообщения пользователя\n2. Отвечай на том же языке\n3. Если пользователь явно просит другой язык - переключись",
                        help_text="How to detect and respond in user's language",
                        verbose_name="Language Detection Rule",
                    ),
                ),
                (
                    "formatting_rules",
                    models.TextField(
                        default="Правила форматирования:\n- Будь дружелюбным и полезным\n- Используй эмодзи умеренно для дружелюбности\n- Структурируй ответы для читаемости",
                        help_text="Emoji usage, message structure",
                        verbose_name="Formatting Rules",
                    ),
                ),
                (
                    "buttons_config",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON config for WAHA Plus interactive buttons/lists",
                        verbose_name="Buttons Configuration",
                    ),
                ),
                (
                    "welcome_buttons",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Buttons for new user welcome message",
                        verbose_name="Welcome Buttons",
                    ),
                ),
                (
                    "error_ai",
                    models.TextField(
                        default="Извините, произошла ошибка. Попробуйте позже.",
                        help_text="Message shown when AI fails",
                        verbose_name="AI Error Message",
                    ),
                ),
                (
                    "error_timeout",
                    models.TextField(
                        default="Сервис не отвечает. Попробуйте позже.",
                        help_text="Message shown on timeout",
                        verbose_name="Timeout Error Message",
                    ),
                ),
                (
                    "error_voice_unavailable",
                    models.TextField(
                        default="Голосовые сообщения временно недоступны. Напишите текстом.",
                        help_text="Message when voice processing fails",
                        verbose_name="Voice Unavailable Message",
                    ),
                ),
            ],
            options={
                "verbose_name": "OTP Bot Prompt Settings",
                "verbose_name_plural": "OTP Bot Prompt Settings",
            },
        ),
    ]
