import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from api_keys.models import InstagramConfig
from .models import InstagramApi


WEBHOOK_URL = "http://161.35.153.151:8080/bot/api/webhook/hiker-key/"

@receiver(post_save, sender=InstagramApi)
@receiver(post_save, sender=InstagramConfig)
def push_key_to_ai_server(sender, instance, **kwargs):
    if instance.is_active and instance.api_key:
        try:
            requests.post(
                WEBHOOK_URL,
                json={'api_key': instance.api_key},
                timeout=2
            )
            print(f"Key synced to {WEBHOOK_URL}")
        except Exception as e:
            print(f"Failed to sync key: {e}")

