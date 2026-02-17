import json
import os
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.storage import default_storage

from organizations.models import Assistant, UserAssistant, Question, Answer, AnswerFile
from shop.models import ShopItem


class AssistantDataService:

    # DATA_DIR = Path(settings.MEDIA_ROOT) / "assistants_data"
    FOLDER_NAME = "assistants_data"

    @classmethod
    def _get_filename(cls, organization):
        safe_title = slugify(organization.title) or "org"
        return f"{safe_title}_{organization.id}.json"

    @classmethod
    def get_file_url(cls, organization):
        """
        Возвращает публичный URL файла из S3 через модель Assistant.
        """
        if not cls.is_assistant_active(organization):
            return None

        try:
            assistant = organization.assistant
            if assistant.catalog_file:
                return assistant.catalog_file.url
        except Assistant.DoesNotExist:
            return None

        return None

    @classmethod
    def is_assistant_active(cls, organization):
        try:
            assistant = organization.assistant
        except Assistant.DoesNotExist:
            return False

        if not assistant.is_enabled:
            return False

        return UserAssistant.objects.filter(
            assistant=assistant,
            is_active=True,
            # active_until__gt=timezone.now() # Раскомментируйте, если нужно проверять дату
        ).exists()

    @classmethod
    def update_organization_json(cls, organization):
        """
        Генерирует JSON и сохраняет его в поле catalog_file модели Assistant.
        """
        try:
            assistant = organization.assistant
        except Assistant.DoesNotExist:
            return

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
                "price": float(item.price) if item.price else "",
                "currency": item.currency.code if item.currency else "",
                "category": item.subcategory.name if item.subcategory else "General",
                "type": item.purchase_type,
                "available": True,
                "url": f"{settings.SITE_URL}/p/{item.id}"
            }
            data_list.append(item_data)

        json_str = json.dumps(data_list, ensure_ascii=False, indent=2)
        file_content = ContentFile(json_str.encode('utf-8'))
        filename = cls._get_filename(organization)

        if assistant.catalog_file:
            assistant.catalog_file.delete(save=False)

        assistant.catalog_file.save(filename, file_content, save=True)
        print(f"✅ S3 JSON updated via Assistant model: {filename}")

    @classmethod
    def delete_organization_json(cls, organization):
        try:
            assistant = organization.assistant
            if assistant.catalog_file:
                assistant.catalog_file.delete(save=True)
        except Assistant.DoesNotExist:
            pass

# @classmethod
#     def delete_json(cls, organization):
#         file_path = cls.get_file_path(organization)
#         if file_path.exists():
#             file_path.unlink()