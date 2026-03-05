from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0191_organization_ai_trial_access"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="gemini_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
