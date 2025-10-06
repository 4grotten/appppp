import json
from pathlib import Path
from django.core.management.base import BaseCommand
from organizations.models import DiscountCard
from django.conf import settings


class Command(BaseCommand):
    help = "Добавляет к организациям информацию про discount"

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / "organization_maps.json"

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"Файл не найден!"))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated_organizations = 0

        for index, org in enumerate(data):
            ids = []
            discount_id = DiscountCard.objects.filter(
                organization_id=org["id"], is_published=True
            )
            if discount_id.exists():
                ids = list(discount_id.values_list("id", flat=True))
                data[index]["discounts"] = ids
                updated_organizations += 1
            else:
                data[index]["discounts"] = []

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.stdout.write(
            self.style.SUCCESS(
                f"SUCCESFULLY UPDATED {updated_organizations} ORGANIZATIONS DISCOUNTS"
            )
        )
