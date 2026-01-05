# Generated manually

from django.db import migrations, models


def migrate_country_to_countries(apps, schema_editor):
    """Переносим данные из country в countries (many-to-many)"""
    RegionalPaymentSystemSettings = apps.get_model('organizations', 'RegionalPaymentSystemSettings')

    # Для каждой записи добавляем текущую страну в новое M2M поле
    for setting in RegionalPaymentSystemSettings.objects.all():
        if hasattr(setting, 'country') and setting.country:
            setting.countries.add(setting.country)

    print(f"Migrated {RegionalPaymentSystemSettings.objects.count()} records")


def reverse_migrate(apps, schema_editor):
    """Обратная миграция - восстанавливаем country из первой страны в countries"""
    RegionalPaymentSystemSettings = apps.get_model('organizations', 'RegionalPaymentSystemSettings')

    for setting in RegionalPaymentSystemSettings.objects.all():
        first_country = setting.countries.first()
        if first_country:
            setting.country = first_country
            setting.save()


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0169_maalypayorganizationpaymentsystem_currencies'),
    ]

    operations = [
        # Шаг 1: Создаем новое поле countries (M2M)
        migrations.AddField(
            model_name='regionalpaymentsystemsettings',
            name='countries',
            field=models.ManyToManyField(
                blank=True,
                help_text='Страны, для которых применяются эти настройки',
                related_name='regional_payment_settings_new',
                to='organizations.Country'
            ),
        ),

        # Шаг 2: Переносим данные из country в countries
        migrations.RunPython(migrate_country_to_countries, reverse_migrate),

        # Шаг 3: Удаляем unique_together
        migrations.AlterUniqueTogether(
            name='regionalpaymentsystemsettings',
            unique_together=set(),
        ),

        # Шаг 4: Удаляем старое поле country
        migrations.RemoveField(
            model_name='regionalpaymentsystemsettings',
            name='country',
        ),

        # Шаг 5: Изменяем related_name у countries на правильный
        migrations.AlterField(
            model_name='regionalpaymentsystemsettings',
            name='countries',
            field=models.ManyToManyField(
                blank=True,
                help_text='Страны, для которых применяются эти настройки',
                related_name='regional_payment_settings',
                to='organizations.Country'
            ),
        ),
    ]
