import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
import threading

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from organizations.models import Assistant
from .models import ShopItem
from .services.comment_services import CommentService
from .tasks import update_assistant_json_task
from shop.services.assistant_data_service import AssistantDataService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ShopItem)
@receiver(post_delete, sender=ShopItem)
def trigger_assistant_json_update(sender, instance, **kwargs):
    if instance.organization:
        if not instance.organization.is_catalog:
            return
        try:
            logger.info(f"[CATALOG_SYNC] Updating JSON for {instance.organization.title}...")
            AssistantDataService.update_organization_json(instance.organization)
            logger.info(f"[CATALOG_SYNC] JSON updated successfully.")

            # Invalidate assistant training data cache
            from messenger_bots.signals import invalidate_assistant_cache
            invalidate_assistant_cache(instance.organization.id, "Catalog JSON updated")

        except Exception as e:
            logger.error(f"[CATALOG_SYNC] Error updating JSON: {e}")


# @receiver(post_save, sender=Assistant)
# def sync_assistant_to_ai_server(sender, instance, **kwargs):

#     def send_request():
#         training_data = CommentService.get_training_data(instance)

#         agent_id = instance.voice_assistant_id

#         if not agent_id:
#             print("Assistant has no voice_assistant_id. Skipping sync.")
#             return

#         url = "http://161.35.153.151:8080/bot/sync-agent/"
#         payload = {
#             "agent_id": agent_id,
#             "training_data": training_data
#         }

#         try:
#             response = requests.post(url, json=payload, timeout=20)
#             if response.status_code == 200:
#                 print(f"Successfully synced agent {agent_id}")
#             else:
#                 print(f"Failed to sync agent: {response.text}")
#         except Exception as e:
#             print(f"Error connecting to AI server: {e}")

#     thread = threading.Thread(target=send_request)
#     thread.start()


