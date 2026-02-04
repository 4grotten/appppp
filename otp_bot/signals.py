"""Signals for OTP Bot models.

Handles cache invalidation when prompt settings are updated.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="otp_bot.OTPBotPromptSettings")
def on_prompt_settings_save(sender, instance, **kwargs):
    """Invalidate prompt cache when settings are saved via Django Admin.

    This ensures that changes made in admin are immediately reflected
    in bot responses without waiting for cache expiration.
    """
    from .services.prompt_service import invalidate_cache

    invalidate_cache()
    logger.info(
        f"[OTP_BOT] Prompt settings updated (is_active={instance.is_active}), "
        "cache invalidated"
    )
