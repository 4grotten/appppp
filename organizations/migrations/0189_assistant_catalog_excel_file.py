from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0188_assistant_catalog_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistant",
            name="catalog_excel_file",
            field=models.FileField(
                blank=True,
                help_text="Excel файл с каталогом товаров",
                null=True,
                upload_to="assistants_data/exports",
            ),
        ),
    ]
