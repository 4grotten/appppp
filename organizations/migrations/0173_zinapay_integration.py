# Generated manually for ZinaPay integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('organizations', '0172_regionalpaymentsystemsettings_is_available_for_ai'),
    ]

    operations = [
        # Add zina_pay_activated field to Organization
        migrations.AddField(
            model_name='organization',
            name='zina_pay_activated',
            field=models.BooleanField(
                default=False,
                help_text='Activated in this organization',
            ),
        ),
        # Add zina_pay_confirmed field to Organization
        migrations.AddField(
            model_name='organization',
            name='zina_pay_confirmed',
            field=models.BooleanField(
                default=False,
                help_text='Available in this organization',
            ),
        ),
        # Create ZinaPayOrganizationPaymentSystem model
        migrations.CreateModel(
            name='ZinaPayOrganizationPaymentSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('api_token', models.CharField(
                    help_text='Bearer token from ZinaPay dashboard',
                    max_length=500,
                )),
                ('webhook_secret', models.CharField(
                    blank=True,
                    help_text='Secret for HMAC webhook signature verification',
                    max_length=256,
                    null=True,
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zina_pay_info',
                    to='organizations.organization',
                )),
                ('currencies', models.ManyToManyField(
                    blank=True,
                    help_text='Supported currencies. Empty = all currencies supported.',
                    related_name='zinapay_configs',
                    to='common.Currency',
                )),
            ],
            options={
                'verbose_name': 'ZinaPay Organization Payment System',
                'verbose_name_plural': 'ZinaPay Organization Payment Systems',
            },
        ),
        # Update RegionalPaymentSystemSettings choices to include ZinaPay (ID 7)
        migrations.AlterField(
            model_name='regionalpaymentsystemsettings',
            name='payment_system_id',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, 'FreedomPay'),
                    (2, 'PaySy'),
                    (3, 'Libersave'),
                    (4, 'Betapay'),
                    (5, 'CryptoCloud'),
                    (6, 'MaalyPay'),
                    (7, 'ZinaPay'),
                ],
                help_text='ID платежной системы (совместим с существующим кодом)',
            ),
        ),
    ]
