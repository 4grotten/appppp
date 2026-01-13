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

    # DATA_DIR = Path(settings.MEDIA_ROOT) / "assistants_data"
    CATALOG_QUESTION_TEXT = "SYSTEM_PRODUCT_CATALOG_HIDDEN"
    # @classmethod
    # def _get_file_path(cls, organization):
    #     cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
    #
    #     safe_title = slugify(organization.title) or "org"
    #     filename = f"{safe_title}_{organization.id}.json"
    #     return cls.DATA_DIR / filename

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
            # active_until__gt=timezone.now()
        ).exists()

        return active_subscription

    @classmethod
    def update_organization_json(cls, organization):
        if not cls.is_assistant_active(organization):
            try:
                question = Question.objects.get(text=cls.CATALOG_QUESTION_TEXT)
                Answer.objects.filter(assistant=organization.assistant, question=question).delete()
                print(f"Catalog removed for expired org: {organization.title}")
            except (Question.DoesNotExist, Assistant.DoesNotExist):
                pass
            return

        items = ShopItem.objects.filter(
            organization=organization,
            is_published=True,
            is_hidden=False
        ).select_related('currency', 'subcategory')

        items_data = []
        for item in items:
            items_data.append({
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": float(item.price) if item.price else 0.0,
                "currency": item.currency.code if item.currency else "KGS",
            })

        cls.save_to_answer_model(organization.assistant, items_data)

    @classmethod
    def save_to_answer_model(cls, assistant: Assistant, data: list):

        file_name = f"catalog_{assistant.organization.id}.json"
        json_content = json.dumps(data, ensure_ascii=False, indent=4)

        with transaction.atomic():

            question, _ = Question.objects.get_or_create(
                text=cls.CATALOG_QUESTION_TEXT,
                defaults={'ordering': 9999}
            )

            answer, created = Answer.objects.get_or_create(
                assistant=assistant,
                question=question,
                defaults={'text': 'System generated catalog file'}
            )

            target_file = None

            if answer.files.exists():
                target_file = answer.files.first()

            if target_file:

                target_file.file.delete(save=False)
                target_file.file.save(file_name, ContentFile(json_content), save=True)
                print(f"Updated existing AnswerFile for {assistant.name}")
            else:

                new_answer_file = AnswerFile()
                new_answer_file.file.save(file_name, ContentFile(json_content), save=True)

                answer.files.add(new_answer_file)
                print(f"Created new AnswerFile for {assistant.name}")

# @classmethod
#     def delete_json(cls, organization):
#         file_path = cls.get_file_path(organization)
#         if file_path.exists():
#             file_path.unlink()