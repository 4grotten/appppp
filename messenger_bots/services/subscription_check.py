"""Subscription and AI status checks for bot message processing."""

import logging
from django.utils import timezone

from messenger_bots.models import TelegramBot, WhatsAppBot

logger = logging.getLogger(__name__)


def check_subscription_active(organization) -> bool:
    """Check if organization has an active subscription.

    Checks both:
    - UserOrgSubscription (organization subscription)
    - UserAssistant (AI assistant subscription)

    If subscription has expired, disables AI on both bots and marks subscription inactive.
    Returns True if subscription is active, False otherwise.
    """
    from organizations.models import UserOrgSubscription, UserAssistant

    # Check 1: UserOrgSubscription (organization subscription)
    org_subscription = (
        UserOrgSubscription.objects
        .filter(organization=organization, is_active=True)
        .order_by('-active_until')
        .first()
    )

    if org_subscription:
        if org_subscription.active_until and org_subscription.active_until < timezone.now():
            # Subscription expired — disable AI on bots
            logger.warning(
                f"[SUB_CHECK] Org subscription expired for org {organization.id} "
                f"(expired at {org_subscription.active_until})"
            )
            org_subscription.is_active = False
            org_subscription.save(update_fields=['is_active'])
            _disable_ai_for_organization(organization)
            return False
        logger.debug(f"[SUB_CHECK] Active org subscription found for org {organization.id}")
        return True

    # Check 2: UserAssistant (AI assistant subscription)
    assistant_subscription = (
        UserAssistant.objects
        .filter(
            assistant__organization=organization,
            is_active=True
        )
        .order_by('-active_until')
        .first()
    )

    if assistant_subscription:
        if assistant_subscription.active_until and assistant_subscription.active_until < timezone.now():
            # Assistant subscription expired — disable AI on bots
            logger.warning(
                f"[SUB_CHECK] Assistant subscription expired for org {organization.id} "
                f"(expired at {assistant_subscription.active_until})"
            )
            assistant_subscription.is_active = False
            assistant_subscription.save(update_fields=['is_active'])
            _disable_ai_for_organization(organization)
            return False
        logger.debug(f"[SUB_CHECK] Active assistant subscription found for org {organization.id}")
        return True

    logger.info(f"[SUB_CHECK] No active subscription for org {organization.id}")
    return False


def _disable_ai_for_organization(organization) -> None:
    """Disable AI for all bots of an organization."""
    tg_updated = TelegramBot.objects.filter(
        organization=organization, is_ai_enabled=True
    ).update(is_ai_enabled=False)

    wa_updated = WhatsAppBot.objects.filter(
        organization=organization, is_ai_enabled=True
    ).update(is_ai_enabled=False)

    if tg_updated or wa_updated:
        logger.info(
            f"[SUB_CHECK] AI disabled for org {organization.id}: "
            f"TG={tg_updated}, WA={wa_updated}"
        )
