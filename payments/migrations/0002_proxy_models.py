# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('organizations', '0173_zinapay_integration'),
    ]

    operations = [
        migrations.CreateModel(
            name='BetapaySettings',
            fields=[],
            options={
                'verbose_name': 'Betapay',
                'verbose_name_plural': 'Betapay - Настройки регионов',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.regionalpaymentsystemsettings',),
        ),
        migrations.CreateModel(
            name='CryptoCloudSettings',
            fields=[],
            options={
                'verbose_name': 'CryptoCloud',
                'verbose_name_plural': 'CryptoCloud - Настройки регионов',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.regionalpaymentsystemsettings',),
        ),
        migrations.CreateModel(
            name='FreedomPaySettings',
            fields=[],
            options={
                'verbose_name': 'FreedomPay',
                'verbose_name_plural': 'FreedomPay - Настройки регионов',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.regionalpaymentsystemsettings',),
        ),
        migrations.CreateModel(
            name='LibersaveSettings',
            fields=[],
            options={
                'verbose_name': 'Libersave',
                'verbose_name_plural': 'Libersave - Настройки регионов',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.regionalpaymentsystemsettings',),
        ),
        migrations.CreateModel(
            name='MaalyPaySettings',
            fields=[],
            options={
                'verbose_name': 'MaalyPay',
                'verbose_name_plural': 'MaalyPay - Настройки регионов',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.regionalpaymentsystemsettings',),
        ),
        migrations.CreateModel(
            name='PaySySettings',
            fields=[],
            options={
                'verbose_name': 'PaySy',
                'verbose_name_plural': 'PaySy - Настройки регионов',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.regionalpaymentsystemsettings',),
        ),
        migrations.CreateModel(
            name='ZinaPayOrganizationPaymentSystem',
            fields=[],
            options={
                'verbose_name': 'Настройки ZinaPay для организации',
                'verbose_name_plural': 'ZinaPay - Настройки организаций',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('organizations.zinapayorganizationpaymentsystem',),
        ),
        migrations.AlterModelOptions(
            name='maalypayorganizationpaymentsystem',
            options={
                'verbose_name': 'Настройки MaalyPay для организации',
                'verbose_name_plural': 'MaalyPay - Настройки организаций',
                'proxy': True,
            },
        ),
    ]
