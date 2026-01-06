# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0171_auto_20260105_1708'),
    ]

    operations = [
        migrations.AddField(
            model_name='regionalpaymentsystemsettings',
            name='is_available_for_ai',
            field=models.BooleanField(
                default=False,
                help_text='Платежка доступна для оплаты AI ассистента (отображается независимо от привязки к организации)',
            ),
        ),
    ]
