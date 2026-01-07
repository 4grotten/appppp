import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import File, ChatGPTSettings
from .tasks import generate_image_versions


@receiver(post_save, sender=File)
def schedule_imagekit_generation(sender, instance: File, created, **kwargs):
    if created and instance.file:
        generate_image_versions.delay(instance.id)


OPENAI_WEBHOOK_URL = "http://161.35.153.151:8080/bot/api/webhook/openai-config/"


@receiver(post_save, sender=ChatGPTSettings)
def sync_openai_to_ai_server(sender, instance, **kwargs):

    if instance.is_active:
        payload = {
            "api_key": instance.api_key,
            "model": instance.model,
            "is_active": instance.is_active
        }

        try:
            requests.post(
                OPENAI_WEBHOOK_URL,
                json=payload,
                timeout=2
            )
            print(f"OpenAI settings synced to {OPENAI_WEBHOOK_URL}")
        except Exception as e:
            print(f"Failed to sync OpenAI settings: {e}")