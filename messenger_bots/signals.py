"""
Signals for invalidating AI assistant cache when training data changes.
"""
import logging

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from organizations.models import Answer

logger = logging.getLogger(__name__)

# Cache version - increment when changing cached data format
# This ensures old cached data is ignored after deployment
ASSISTANT_CACHE_VERSION = "v1"


def get_assistant_cache_key(organization_id: int) -> str:
    """
    Get cache key for assistant training data.
    Centralized to ensure consistency across read/write/invalidate operations.
    Increment ASSISTANT_CACHE_VERSION when changing data format.
    """
    return f"{ASSISTANT_CACHE_VERSION}:assistant_training_data:{organization_id}"


def invalidate_assistant_cache(organization_id: int, reason: str = ""):
    """
    Invalidate the cached training data for an organization.
    Next request will load fresh data, and the periodic task will re-cache it.
    """
    cache_key = get_assistant_cache_key(organization_id)
    deleted = cache.delete(cache_key)

    # Also bump response cache version so old AI answers are ignored immediately.
    # This prevents stale responses after training data updates.
    response_version_key = f"ai_response_ver:{organization_id}"
    try:
        previous_version = cache.get(response_version_key) or 1
        new_version = cache.incr(response_version_key)
    except ValueError:
        previous_version = 1
        cache.set(response_version_key, 2, timeout=None)
        new_version = 2

    logger.info(
        f"[CACHE_INVALIDATE] Response cache version org={organization_id}: "
        f"{previous_version} -> {new_version}, reason={reason}"
    )

    if deleted:
        logger.info(f"[CACHE_INVALIDATE] Cleared cache for org {organization_id}: {reason}")
    else:
        logger.info(f"[CACHE_INVALIDATE] Response cache version bumped for org {organization_id}: {reason}")
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
        for answer in instance.answers.select_related('assistant'):
            org_id = answer.assistant.organization_id
            invalidate_assistant_cache(org_id, "AnswerFile updated")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on AnswerFile save: {e}")


@receiver(post_delete, sender='organizations.AnswerFile')
def invalidate_cache_on_answer_file_delete(sender, instance, **kwargs):
    """Invalidate cache when AnswerFile is deleted."""
    try:
        for answer in instance.answers.select_related('assistant'):
            org_id = answer.assistant.organization_id
            invalidate_assistant_cache(org_id, "AnswerFile deleted")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on AnswerFile delete: {e}")


@receiver(m2m_changed, sender=Answer.files.through)
def invalidate_cache_on_answer_files_changed(sender, instance, action, **kwargs):
    """Invalidate cache when files are attached/detached from Answer."""
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    try:
        org_id = instance.assistant.organization_id
        invalidate_assistant_cache(org_id, f"Answer files changed ({action})")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on Answer.files m2m change: {e}")


@receiver(post_save, sender='organizations.Assistant')
def invalidate_cache_on_assistant_save(sender, instance, **kwargs):
    """Invalidate cache when Assistant settings are updated."""
    try:
        org_id = instance.organization_id
        invalidate_assistant_cache(org_id, "Assistant updated")
    except Exception as e:
        logger.error(f"[CACHE_INVALIDATE] Error on Assistant save: {e}")
