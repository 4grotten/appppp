"""Subscription and AI status checks for bot message processing."""

import logging
from django.utils import timezone

from messenger_bots.models import TelegramBot, WhatsAppBot
from organizations.services.ai_access_service import check_ai_feature_access

logger = logging.getLogger(__name__)


def check_subscription_active(organization, feature: str = "general") -> bool:
    """Check if organization has an active subscription.

    Checks both:
    - UserOrgSubscription (organization subscription)
    - UserAssistant (AI assistant subscription)

    Returns True if paid subscription is active or trial allows the feature.
    If paid subscription expired and trial is not active, disables AI on both bots.
    """
    from organizations.models import UserOrgSubscription, UserAssistant
    has_expired_paid_subscription = False

    # Check 1: UserOrgSubscription (organization subscription)
    org_subscription = (
        UserOrgSubscription.objects
        .filter(organization=organization, is_active=True)
        .order_by('-active_until')
        .first()
    )

    if org_subscription:
        if org_subscription.active_until and org_subscription.active_until < timezone.now():
            logger.warning(
                f"[SUB_CHECK] Org subscription expired for org {organization.id} "
                f"(expired at {org_subscription.active_until})"
            )
            org_subscription.is_active = False
            org_subscription.save(update_fields=['is_active'])
            has_expired_paid_subscription = True
        logger.debug(f"[SUB_CHECK] Active org subscription found for org {organization.id}")
        if org_subscription.is_active:
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
            logger.warning(
                f"[SUB_CHECK] Assistant subscription expired for org {organization.id} "
                f"(expired at {assistant_subscription.active_until})"
            )
            assistant_subscription.is_active = False
            assistant_subscription.save(update_fields=['is_active'])
            has_expired_paid_subscription = True
        logger.debug(f"[SUB_CHECK] Active assistant subscription found for org {organization.id}")
        if assistant_subscription.is_active:
            return True

    if check_ai_feature_access(organization=organization, feature=feature):
        logger.info(
            "[SUB_CHECK] Trial access granted for org %s (feature=%s)",
            organization.id,
            feature,
        )
        return True

    if has_expired_paid_subscription:
        _disable_ai_for_organization(organization)

    logger.info(
        "[SUB_CHECK] No paid subscription or trial access for org %s (feature=%s)",
        organization.id,
        feature,
    )
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
