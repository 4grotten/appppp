# Generated manually on 2026-01-19
# Migration for AIPromptSettings model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0069_merge_20260109_0922'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIPromptSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('language_instruction_ru', models.TextField(
                    default='Отвечай на Русском языке.',
                    verbose_name='Language Instruction (Russian)',
                    help_text='Инструкция для ответа на русском языке'
                )),
                ('language_instruction_en', models.TextField(
                    default='Answer strictly in ENGLISH. Translate all data from Russian to English.',
                    verbose_name='Language Instruction (English)',
                    help_text='Инструкция для ответа на английском языке'
                )),
                ('identity_template', models.TextField(
                    default='You are {assistant_name}, an assistant at {organization}.\nPosition: {position}. Gender: {gender}.',
                    verbose_name='Identity Template',
                    help_text='Шаблон идентичности ассистента. Переменные: {assistant_name}, {organization}, {position}, {gender}'
                )),
                ('formatting_rules', models.TextField(
                    default=(
                        '⛔ STRICT FORMATTING RULES:\n'
                        '1. NO MARKDOWN. No *, **, ~ , [text](url).\n'
                        '2. Send LINKS as plain text only.\n'
                        "3. SEPARATOR: Use '###NEXT###' to separate different products or the final link."
                    ),
                    verbose_name='Formatting Rules',
                    help_text='Правила форматирования ответов'
                )),
                ('scenario_a_discounts', models.TextField(
                    default=(
                        'scenario_A: DISCOUNTS & COUPONS\n'
                        '   - IF user asks about discounts, coupons, or bonuses:\n'
                        '   - Answer ONLY about the promotions.\n'
                        '   - DO NOT list products/items unless the user explicitly asks for them.\n'
                        '   - DO NOT use the ###NEXT### tag in this scenario.'
                    ),
                    verbose_name='Scenario A: Discounts',
                    help_text='Инструкции для обработки вопросов о скидках'
                )),
                ('scenario_b_products', models.TextField(
                    default=(
                        'scenario_B: PRODUCTS (Catalogue)\n'
                        '   ⚠️ CRITICAL: You MUST use this EXACT format for EACH product:\n'
                        '   - DO NOT use dashes (-) or bullet points!\n'
                        '   - Put ###NEXT### BETWEEN each product (not at the end)\n\n'
                        '   CORRECT FORMAT:\n'
                        '   Item: <item name from catalog>\n'
                        '   Price: <price from catalog>\n'
                        '   URL: <item url from catalog>\n'
                        '   ###NEXT###\n'
                        '   Item: <item name from catalog>\n'
                        '   Price: <price from catalog>\n'
                        '   URL: <item url from catalog>'
                    ),
                    verbose_name='Scenario B: Products',
                    help_text='Инструкции для обработки запросов о товарах'
                )),
                ('scenario_c_contacts', models.TextField(
                    default=(
                        'scenario_C: CONTACTS\n'
                        '   - IF user asks for contacts/address/phone:\n'
                        "   - 1. First check the 'KNOWLEDGE BASE' (files/answers) below.\n"
                        "   - 2. If not found, use 'ORGANIZATION DATA' below.\n"
                        '   - Required Format:\n'
                        '     📞 Phone: <Value>\n'
                        '     🏢 Address: <Value>\n'
                        '     🕘 Hours: <Value> - <Value>'
                    ),
                    verbose_name='Scenario C: Contacts',
                    help_text='Инструкции для обработки запросов о контактах'
                )),
                ('scenario_d_general', models.TextField(
                    default=(
                        'scenario_D: GENERAL QUESTIONS\n'
                        '   - IF user asks general questions (Привет, Что ты умеешь?, Hello, etc.):\n'
                        '   - Answer naturally and helpfully.\n'
                        '   - Briefly describe what you can help with (products, promotions, contacts).\n'
                        '   - DO NOT use ###NEXT### tag.\n'
                        '   - DO NOT list products unless asked.'
                    ),
                    verbose_name='Scenario D: General Questions',
                    help_text='Инструкции для обработки общих вопросов (приветствия и т.д.)'
                )),
                ('ending_rule', models.TextField(
                    default=(
                        '🏁 ENDING RULE:\n'
                        '   - ONLY when listing products, finish with organization link.\n'
                        '   - Format: ###NEXT###\nMore items at: {org_page_url}'
                    ),
                    verbose_name='Ending Rule',
                    help_text='Правило завершения ответа. Переменная: {org_page_url}'
                )),
                ('few_shot_example_greeting_ru', models.TextField(
                    default='Здравствуйте! Я помощник {organization}. Могу помочь с информацией о товарах, акциях и контактах. Чем могу быть полезен?',
                    verbose_name='Greeting Example (RU)',
                    help_text='Пример ответа на приветствие (рус). Переменная: {organization}'
                )),
                ('few_shot_example_greeting_en', models.TextField(
                    default="Hello! I'm an assistant at {organization}. I can help with product info, promotions, and contacts. How can I help you?",
                    verbose_name='Greeting Example (EN)',
                    help_text='Пример ответа на приветствие (англ). Переменная: {organization}'
                )),
                ('few_shot_example_capabilities_ru', models.TextField(
                    default='Я могу помочь вам с информацией о товарах в {organization}, рассказать об акциях и скидках, предоставить контактные данные и адрес. Задавайте вопросы!',
                    verbose_name='Capabilities Example (RU)',
                    help_text="Пример ответа на 'что ты умеешь' (рус)"
                )),
                ('few_shot_example_capabilities_en', models.TextField(
                    default='I can help you with product information at {organization}, tell you about promotions and discounts, provide contact details and address. Feel free to ask!',
                    verbose_name='Capabilities Example (EN)',
                    help_text="Пример ответа на 'what can you do' (англ)"
                )),
                ('few_shot_example_contacts', models.TextField(
                    default='📞 Телефон: +7 XXX XXX-XX-XX\n🏢 Адрес: ул. Примерная, 1\n🕘 Часы работы: 10:00 - 20:00',
                    verbose_name='Contacts Example',
                    help_text='Пример ответа на запрос контактов'
                )),
                ('search_rules', models.TextField(
                    default=(
                        'SEARCH RULES:\n'
                        "- Extract keywords from user question (e.g. 'купальник', 'кроссовки')\n"
                        '- Search ENTIRE catalog for items matching keywords in name/category/description\n'
                        '- If found - show ALL matching products, not just first ones\n'
                        '- If not found - say so and suggest similar categories'
                    ),
                    verbose_name='Search Rules',
                    help_text='Правила поиска по каталогу'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    verbose_name='Active',
                    help_text='Если выключено, используются дефолтные промпты из кода'
                )),
            ],
            options={
                'verbose_name': 'AI Prompt Settings',
                'verbose_name_plural': 'AI Prompt Settings',
            },
        ),
    ]
