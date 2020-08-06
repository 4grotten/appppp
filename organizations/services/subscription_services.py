from notifications.constants import (
    SUBSCRIPTION_NOTIFICATION_MODE, FOLLOWED_TO_ORGANIZATION_TYPE,
    FOLLOWED_TO_ORGANIZATION_TITLE, ORGANIZATION_FOLLOWED_TYPE,
    ORGANIZATION_FOLLOWED_TITLE)
from notifications.services import NotificationService
from notifications.tasks import sent_notification
from organizations.models import Organization, Subscription
from django.db.models import QuerySet
from users.models import User


class SubscriptionService:
    @classmethod
    def is_subscribed(cls, organization: Organization, user: User) -> bool:
        return Subscription.objects.filter(organization=organization, user=user).exists()

    @classmethod
    def get_number_of_subscriptions(cls, organization: Organization) -> int:
        return Subscription.objects.filter(organization=organization).count()

    @classmethod
    def toggle_subscription_status(cls, organization: Organization, user: User) -> bool:
        subscription, created = Subscription.objects.get_or_create(organization=organization, user=user)
        if created:
            sent_notification(
                recipient=organization.owner,
                sender=user,
                mode=SUBSCRIPTION_NOTIFICATION_MODE,
                notification_type=FOLLOWED_TO_ORGANIZATION_TYPE,
                title=FOLLOWED_TO_ORGANIZATION_TITLE,
                description=organization.address,
                organization=organization
            )

            sent_notification(
                recipient=user,
                mode=SUBSCRIPTION_NOTIFICATION_MODE,
                notification_type=ORGANIZATION_FOLLOWED_TYPE,
                title=ORGANIZATION_FOLLOWED_TITLE.format(org_title=organization.title),
                description=organization.address,
                organization=organization
            )

            return True
        subscription.delete()
        return False

    @classmethod
    def get_user_subscriptions(cls, user: User) -> QuerySet:
        organizations_id = Subscription.objects.filter(user=user)
        organizations = Organization.objects.filter(id__in=organizations_id.values('organization_id')).distinct()
        return organizations
