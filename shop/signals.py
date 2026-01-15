from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import ShopItem
from .tasks import update_assistant_json_task
from shop.services.assistant_data_service import AssistantDataService

@receiver(post_save, sender=ShopItem)
@receiver(post_delete, sender=ShopItem)
def trigger_assistant_json_update(sender, instance, **kwargs):
    if instance.organization:
        try:
            
            print(f"🔄 [SYNC] Обновляем JSON для {instance.organization.title}...")
            AssistantDataService.update_organization_json(instance.organization)
            print(f"✅ [SYNC] JSON обновлен успешно.")
        except Exception as e:
            print(f"❌ [SYNC] Ошибка обновления JSON: {e}")