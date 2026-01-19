import logging
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from api_keys.models import ChatGPTConfig
from .models import File, ChatGPTSettings, AIPromptSettings
from .tasks import generate_image_versions

logger = logging.getLogger(__name__)


@receiver(post_save, sender=File)
def schedule_imagekit_generation(sender, instance: File, created, **kwargs):
    if created and instance.file:
        specs = [
            "common:file:large",
            "common:file:medium",
            "common:file:small"
        ]

        for spec in specs:
            generate_image_versions.delay(instance.file.name, spec)


# ============== Webhook URLs ==============
AI_ASSISTANT_BASE_URL = "http://161.35.153.151:8080"
OPENAI_WEBHOOK_URL = f"{AI_ASSISTANT_BASE_URL}/bot/api/webhook/openai-config/"
PROMPT_WEBHOOK_URL = f"{AI_ASSISTANT_BASE_URL}/bot/api/webhook/prompt-config/"


@receiver(post_save, sender=ChatGPTSettings)
@receiver(post_save, sender=ChatGPTConfig)
def sync_openai_to_ai_server(sender, instance, **kwargs):
    """Sync OpenAI API settings to ai_assistant server."""
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
            logger.info(f"OpenAI settings synced to {OPENAI_WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"Failed to sync OpenAI settings: {e}")


@receiver(post_save, sender=AIPromptSettings)
def sync_prompts_to_ai_server(sender, instance, **kwargs):
    """
    Sync AI prompt settings to ai_assistant server.
    Called when AIPromptSettings is saved from Django admin.
    """
    if not instance.is_active:
        # Send empty dict to signal using defaults
        payload = {"is_active": False}
    else:
        payload = AIPromptSettings.get_prompt_data()

    try:
        response = requests.post(
            PROMPT_WEBHOOK_URL,
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            logger.info(f"AI prompts synced to {PROMPT_WEBHOOK_URL}")
        else:
            logger.warning(f"Prompt sync returned status {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to sync AI prompts: {e}")