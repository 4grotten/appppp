import json
import os
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from organizations.models import Assistant, UserAssistant, Question, Answer, AnswerFile
from shop.models import ShopItem


class AssistantDataService:

    DATA_DIR = Path(settings.MEDIA_ROOT) / "assistants_data"

    @classmethod
    def _get_file_path(cls, organization):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

        safe_title = slugify(organization.title) or "org"
        filename = f"{safe_title}_{organization.id}.json"
        return cls.DATA_DIR / filename

    @classmethod
    def is_assistant_active(cls, organization):
        try:
            assistant = organization.assistant
        except Assistant.DoesNotExist:
            return False

        if not assistant.is_enabled:
            return False

        active_subscription = UserAssistant.objects.filter(
            assistant=assistant,
            is_active=True,
            active_until__gt=timezone.now()
        ).exists()

        return active_subscription

    @classmethod
    def update_organization_json(cls, organization):
        if not cls.is_assistant_active(organization):
            cls.delete_organization_json(organization)
            return

        items = ShopItem.objects.filter(
            organization=organization,
            is_published=True,
            is_hidden=False,
            organization__is_active=True,
            organization__is_deleted=False
        ).select_related('currency', 'subcategory')

        data_list = []
        for item in items:

            item_data = {
                "id": item.id,
                "name": item.name,
                "description": item.description or "",
                "price": float(item.price) if item.price else None,
                "currency": item.currency.code if item.currency else None,
                "category": item.subcategory.name if item.subcategory else "General",
                "type": item.purchase_type,
                "available": True,
                "url": f"/item/{item.id}"
            }
            data_list.append(item_data)


        file_path = cls._get_file_path(organization)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
            print(f"JSON updated for {organization.title}: {file_path}")
        except Exception as e:
            print(f"Error writing JSON for assistant: {e}")

    @classmethod
    def delete_organization_json(cls, organization):
        file_path = cls._get_file_path(organization)
        if file_path.exists():
            try:
                os.remove(file_path)
            except OSError:
                pass

# @classmethod
#     def delete_json(cls, organization):
#         file_path = cls.get_file_path(organization)
#         if file_path.exists():
#             file_path.unlink()