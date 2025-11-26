import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from organizations.models import Organization


class Command(BaseCommand):
    help = "Uploads image sizes to organization_maps.json"

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / "organization_maps.json"

        if not file_path.exists():
            self.stdout.write(self.style.ERROR("Cannot open file"))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated_organization = 0

        for index, org in enumerate(data):
            ids = []
            organization = (
                Organization.objects.filter(pk=org["id"])
                .select_related("image")
                .first()
            )

            if organization and organization.image:
                image_medium = organization.image.medium_property
                image_large = organization.image.large_property
                data[index]["image"]["medium"] = image_medium
                data[index]["image"]["large"] = image_large
                updated_organization += 1

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(self.style.WARNING(f"WRITING TO: {file_path.resolve()}"))

        self.stdout.write(
            self.style.SUCCESS(f"SUCCESFULLY UPDATED {updated_organization} org IMAGES")
        )
