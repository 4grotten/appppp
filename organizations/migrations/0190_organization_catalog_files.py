from django.db import migrations, models


def copy_catalog_fields_from_assistant(apps, schema_editor):
    Assistant = apps.get_model("organizations", "Assistant")

    assistants = Assistant.objects.select_related("organization").all().iterator()
    for assistant in assistants:
        organization = assistant.organization
        changed_fields = []

        if assistant.catalog_file and not organization.catalog_file:
            organization.catalog_file = assistant.catalog_file
            changed_fields.append("catalog_file")

        if assistant.catalog_excel_file and not organization.catalog_excel_file:
            organization.catalog_excel_file = assistant.catalog_excel_file
            changed_fields.append("catalog_excel_file")

        if changed_fields:
            organization.save(update_fields=changed_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0189_assistant_catalog_excel_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="catalog_file",
            field=models.FileField(
                blank=True,
                help_text="JSON файл с каталогом товаров",
                null=True,
                upload_to="assistants_data",
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="catalog_excel_file",
            field=models.FileField(
                blank=True,
                help_text="Excel файл с каталогом товаров",
                null=True,
                upload_to="assistants_data/exports",
            ),
        ),
        migrations.RunPython(
            copy_catalog_fields_from_assistant, migrations.RunPython.noop
        ),
    ]
