import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def has_active_paid_ai_access(organization) -> bool:
    from organizations.models import UserAssistant, UserOrgSubscription

    now = timezone.now()

    has_org_subscription = UserOrgSubscription.objects.filter(
        organization=organization,
        is_active=True,
    ).filter(active_until__isnull=True).exists() or UserOrgSubscription.objects.filter(
        organization=organization,
        is_active=True,
        active_until__gte=now,
    ).exists()

    if has_org_subscription:
        return True

    return UserAssistant.objects.filter(
        assistant__organization=organization,
        is_active=True,
    ).filter(active_until__isnull=True).exists() or UserAssistant.objects.filter(
        assistant__organization=organization,
        is_active=True,
        active_until__gte=now,
    ).exists()


def check_ai_feature_access(organization, feature: str = "general") -> bool:
    if has_active_paid_ai_access(organization):
        logger.debug(
            "[AI_ACCESS] Paid access granted: org=%s, feature=%s",
            organization.id,
            feature,
        )
        return True

    trial_active = organization.is_ai_trial_active(feature=feature)
    logger.info(
        "[AI_ACCESS] Trial access check: org=%s, feature=%s, allowed=%s, trial_enabled=%s, trial_ends_at=%s",
        organization.id,
        feature,
        trial_active,
        organization.ai_trial_enabled,
        organization.ai_trial_ends_at,
    )
    return trial_active


def check_gemini_access(organization) -> bool:
    """Return Gemini access based on explicit flag or active AI access."""
    if organization.gemini_enabled:
        logger.info(
            "[GEMINI_ACCESS] Flag access granted: org=%s",
            organization.id,
        )
        return True

    subscription_or_trial_access = check_ai_feature_access(
        organization=organization,
        feature="general",
    )
    logger.info(
        "[GEMINI_ACCESS] Subscription/trial access for org=%s: %s",
        organization.id,
        subscription_or_trial_access,
    )
    return subscription_or_trial_access
