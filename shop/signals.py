from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import ShopItem
from .tasks import update_assistant_json_task

@receiver(post_save, sender=ShopItem)
@receiver(post_delete, sender=ShopItem)
def trigger_assistant_json_update(sender, instance, **kwargs):
    if instance.organization:

        transaction.on_commit(
            lambda: update_assistant_json_task.delay(instance.organization.id)
        )