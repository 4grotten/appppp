# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('organizations', '0168_maalypayorganizationpaymentsystem_bank_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='maalypayorganizationpaymentsystem',
            name='currencies',
            field=models.ManyToManyField(
                blank=True,
                help_text='Supported currencies. Empty = all currencies supported.',
                related_name='maalypay_configs',
                to='common.Currency',
            ),
        ),
    ]
