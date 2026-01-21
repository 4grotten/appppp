# Generated manually on 2026-01-20
# Update default values for AIPromptSettings fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0071_aipromptsettings_language_detection_rule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aipromptsettings',
            name='ending_rule',
            field=models.TextField(
                default=(
                    "🏁 ENDING RULE:\n"
                    "   - ONLY when listing products, finish with organization link.\n"
                    "   - Russian: ###NEXT###\nБольше товаров на странице: {org_page_url}\n"
                    "   - English: ###NEXT###\nMore items at: {org_page_url}"
                ),
                help_text='Правило завершения ответа. Переменная: {org_page_url}',
                verbose_name='Ending Rule',
            ),
        ),
        migrations.AlterField(
            model_name='aipromptsettings',
            name='language_instruction_en',
            field=models.TextField(
                default='Answer strictly in ENGLISH. Translate all data from Russian to English.',
                help_text='Инструкция для ответа на английском языке (для обратной совместимости)',
                verbose_name='Language Instruction (English)',
            ),
        ),
        migrations.AlterField(
            model_name='aipromptsettings',
            name='language_instruction_ru',
            field=models.TextField(
                default='Отвечай на Русском языке.',
                help_text='Инструкция для ответа на русском языке (для обратной совместимости)',
                verbose_name='Language Instruction (Russian)',
            ),
        ),
        migrations.AlterField(
            model_name='aipromptsettings',
            name='scenario_b_products',
            field=models.TextField(
                default=(
                    "scenario_B: PRODUCTS (Catalogue)\n"
                    "   ⚠️ CRITICAL: You MUST use this EXACT format for EACH product:\n"
                    "   - DO NOT use dashes (-) or bullet points!\n"
                    "   - DO NOT copy the DATA: format from catalog!\n"
                    "   - Put ###NEXT### BETWEEN each product (not at the end)\n\n"
                    "   FORMAT for Russian:\n"
                    "   Товар: <item name>\n"
                    "   Цена: <price>\n"
                    "   Ссылка: <url>\n"
                    "   ###NEXT###\n"
                    "   FORMAT for English:\n"
                    "   Product: <item name>\n"
                    "   Price: <price>\n"
                    "   Link: <url>"
                ),
                help_text='Инструкции для обработки запросов о товарах. ВАЖНО: Используйте \'Товар/Product\' и \'Ссылка/Link\' для корректного парсинга в TG боте',
                verbose_name='Scenario B: Products',
            ),
        ),
        migrations.AlterField(
            model_name='aipromptsettings',
            name='scenario_c_contacts',
            field=models.TextField(
                default=(
                    "scenario_C: CONTACTS\n"
                    "   - IF user asks for contacts/address/phone:\n"
                    "   - 1. First check the 'KNOWLEDGE BASE' (files/answers) below.\n"
                    "   - 2. If not found, use 'ORGANIZATION DATA' below.\n"
                    "   - Format for Russian: 📞 Телефон: / 🏢 Адрес: / 🕘 Часы работы:\n"
                    "   - Format for English: 📞 Phone: / 🏢 Address: / 🕘 Hours:"
                ),
                help_text='Инструкции для обработки запросов о контактах',
                verbose_name='Scenario C: Contacts',
            ),
        ),
    ]
