from typing import Any, Optional

from django.core.management.base import BaseCommand
from django.db.models import F
from shop.models import ShopItem


class Command(BaseCommand):
    help = "Change price of items in organization with id 2784"

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        ShopItem.objects.filter(organization_id=2784).update(price=F("price") * 4)
        self.stdout.write(self.style.SUCCESS("Prices updated successfully."))
        return None