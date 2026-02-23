import json
import os
import logging
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.storage import default_storage

from organizations.models import Assistant, UserAssistant, Question, Answer, AnswerFile
from shop.models import ShopItem

logger = logging.getLogger(__name__)


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
        Возвращает публичный URL файла каталога.
        """
        if getattr(organization, "catalog_file", None):
            logger.info(
                f"[CATALOG_SOURCE] Organization catalog_file used for org_id={organization.id}"
            )
            return organization.catalog_file.url

        try:
            assistant = organization.assistant
            if assistant.catalog_file:
                logger.info(
                    f"[CATALOG_SOURCE] Assistant catalog_file fallback used for org_id={organization.id}"
                )
                return assistant.catalog_file.url
        except Assistant.DoesNotExist:
            logger.info(
                f"[CATALOG_SOURCE] No catalog source found (no assistant) for org_id={organization.id}"
            )
            return None

        logger.info(
            f"[CATALOG_SOURCE] No catalog file in Organization or Assistant for org_id={organization.id}"
        )
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
        Генерирует JSON и сохраняет его в поле catalog_file модели Organization.
        """
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
                "discount": float(item.discount) if item.discount else "",
                "discount_price": float(item.discounted_price) if item.discounted_price else "",
                "currency": item.currency.code if item.currency else "",
                "category": item.subcategory.name if item.subcategory else "General",
                "type": item.purchase_type,
                "available": True,
                "url": f"{settings.SITE_URL}/p/{item.id}",
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            data_list.append(item_data)

        json_str = json.dumps(data_list, ensure_ascii=False, indent=2)
        file_content = ContentFile(json_str.encode('utf-8'))
        filename = cls._get_filename(organization)

        if getattr(organization, "catalog_file", None):
            logger.info(
                f"[CATALOG_SAVE] Deleting previous Organization catalog_file for org_id={organization.id}"
            )
            organization.catalog_file.delete(save=False)

        organization.catalog_file.save(filename, file_content, save=True)
        file_url = organization.catalog_file.url
        logger.info(
            f"[CATALOG_SAVE] Saved catalog_file to Organization for org_id={organization.id}"
        )
        logger.info(f"✅ Catalog JSON updated for {organization.title} (ID: {organization.id})")
        logger.info(f"   📁 Filename: {filename}")
        logger.info(f"   🔗 URL: {file_url}")
        print(f"✅ S3 JSON updated via: {filename}")

    @classmethod
    def delete_organization_json(cls, organization):
        if getattr(organization, "catalog_file", None):
            filename = organization.catalog_file.name
            organization.catalog_file.delete(save=True)
            logger.info(
                f"[CATALOG_DELETE] Deleted Organization catalog_file for org_id={organization.id}"
            )
            logger.info(f"❌ Catalog JSON deleted for {organization.title} (ID: {organization.id})")
            logger.info(f"   📁 Deleted filename: {filename}")
            return

        try:
            assistant = organization.assistant
            if assistant.catalog_file:
                filename = assistant.catalog_file.name
                assistant.catalog_file.delete(save=True)
                logger.info(
                    f"[CATALOG_DELETE] Deleted Assistant catalog_file fallback for org_id={organization.id}"
                )
                logger.info(f"❌ Legacy catalog JSON deleted for {organization.title} (ID: {organization.id})")
                logger.info(f"   📁 Deleted filename: {filename}")
        except Assistant.DoesNotExist:
            pass

# @classmethod
#     def delete_json(cls, organization):
#         file_path = cls.get_file_path(organization)
#         if file_path.exists():
#             file_path.unlink()