import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import ShopItem
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