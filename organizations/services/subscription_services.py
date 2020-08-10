from django.db.models import QuerySet, Subquery, OuterRef

from notifications.constants import (
    FOLLOWED_TO_ORGANIZATION_TYPE,
    FOLLOWED_TO_ORGANIZATION_TITLE, ORGANIZATION_FOLLOWED_TYPE,
    ORGANIZATION_FOLLOWED_TITLE, SUBSCRIPTION_NOTIFICATION_DESCRIPTION, PERSONAL_MODE)
from organizations.models import Organization, Subscription
from django.db.models import QuerySet
from users.models import User
from notifications.tasks import sent_notification


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
            sent_notification.delay(
                recipient_id=organization.owner_id,
                sender_id=user.id,
                mode=PERSONAL_MODE,
                notification_type=FOLLOWED_TO_ORGANIZATION_TYPE,
                title=FOLLOWED_TO_ORGANIZATION_TITLE,
                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                organization_id=organization.id
            )

            sent_notification.delay(
                recipient_id=user.id,
                mode=PERSONAL_MODE,
                notification_type=ORGANIZATION_FOLLOWED_TYPE,
                title=ORGANIZATION_FOLLOWED_TITLE.format(org_title=organization.title),
                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                organization_id=organization.id
            )

            return True
        subscription.delete()
        return False

    @classmethod
    def get_user_subscriptions(cls, user: User) -> QuerySet:
        organizations = Organization.objects.filter(id__in=user.subscriptions.values('organization_id')).annotate(
            subscription_time=Subquery(
                Subscription.objects.filter(organization=OuterRef('pk'), user=user).values('created_at')[:1])
        ).order_by('-subscription_time')
        return organizations
