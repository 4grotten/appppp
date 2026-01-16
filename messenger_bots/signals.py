"""
Signals for invalidating AI assistant cache when training data changes.
"""
import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

logger = logging.getLogger(__name__)


def invalidate_assistant_cache(organization_id: int, reason: str = ""):
    """
    Invalidate the cached training data for an organization.
    Next request will load fresh data, and the periodic task will re-cache it.
    """
    cache_key = f"assistant_training_data:{organization_id}"
    deleted = cache.delete(cache_key)
    if deleted:
        logger.info(f"[CACHE_INVALIDATE] Cleared cache for org {organization_id}: {reason}")
    return deleted


@receiver(post_save, sender='organizations.Answer')
def invalidate_cache_on_answer_save(sender, instance, created, **kwargs):
    """Invalidate cache when an Answer is created or updated."""
    try:
        org_id = instance.assistant.organization_id
        action = "created" if created else "updated"
        invalidate_assistant_cache(org_id, f"Answer {action}")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on Answer save: {e}")


@receiver(post_delete, sender='organizations.Answer')
def invalidate_cache_on_answer_delete(sender, instance, **kwargs):
    """Invalidate cache when an Answer is deleted."""
    try:
        org_id = instance.assistant.organization_id
        invalidate_assistant_cache(org_id, "Answer deleted")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on Answer delete: {e}")


@receiver(post_save, sender='organizations.AnswerFile')
def invalidate_cache_on_answer_file_save(sender, instance, **kwargs):
    """Invalidate cache when AnswerFile is added."""
    try:
        org_id = instance.answer.assistant.organization_id
        invalidate_assistant_cache(org_id, "AnswerFile added")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on AnswerFile save: {e}")


@receiver(post_delete, sender='organizations.AnswerFile')
def invalidate_cache_on_answer_file_delete(sender, instance, **kwargs):
    """Invalidate cache when AnswerFile is deleted."""
    try:
        org_id = instance.answer.assistant.organization_id
        invalidate_assistant_cache(org_id, "AnswerFile deleted")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on AnswerFile delete: {e}")


@receiver(post_save, sender='organizations.Assistant')
def invalidate_cache_on_assistant_save(sender, instance, **kwargs):
    """Invalidate cache when Assistant settings are updated."""
    try:
        org_id = instance.organization_id
        invalidate_assistant_cache(org_id, "Assistant updated")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on Assistant save: {e}")
