from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0190_organization_catalog_files"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="ai_trial_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="organization",
            name="ai_trial_ends_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="ai_trial_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="ai_trial_telegram_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="ai_trial_web_chat_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="ai_trial_whatsapp_enabled",
            field=models.BooleanField(default=True),
        ),
    ]
