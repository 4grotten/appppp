import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('common', '0072_alter_aipromptsettings_defaults'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedContact',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=255, verbose_name='Full Name')),
                ('phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Phone')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email')),
                ('company', models.CharField(blank=True, max_length=255, null=True, verbose_name='Company')),
                ('position', models.CharField(blank=True, max_length=255, null=True, verbose_name='Position')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('payment_methods', models.JSONField(blank=True, default=list, help_text='Array of PaymentMethod objects: [{id, type, label, value, network?}]', verbose_name='Payment Methods')),
                ('social_links', models.JSONField(blank=True, default=list, help_text='Array of ContactSocialLink objects: [{id, networkId, networkName, url}]', verbose_name='Social Links')),
                ('avatar', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='saved_contact_avatars', to='common.file', verbose_name='Avatar')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_contacts', to=settings.AUTH_USER_MODEL, verbose_name='Owner')),
            ],
            options={
                'verbose_name': 'Saved Contact',
                'verbose_name_plural': 'Saved Contacts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='savedcontact',
            index=models.Index(fields=['user', '-created_at'], name='saved_conta_user_id_c62b6a_idx'),
        ),
        migrations.AddIndex(
            model_name='savedcontact',
            index=models.Index(fields=['full_name'], name='saved_conta_full_na_a04c60_idx'),
        ),
    ]
