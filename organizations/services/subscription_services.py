from django.db.models import QuerySet
from django.db.models import Subquery, OuterRef
from django.utils.translation import gettext_lazy as _

from common.exceptions import PermissionDeniedException, ObjectNotFoundException
from notifications.constants import (
    FOLLOWED_TO_ORGANIZATION_TYPE,
    FOLLOWED_TO_ORGANIZATION_TITLE, ORGANIZATION_FOLLOWED_TYPE,
    ORGANIZATION_FOLLOWED_TITLE, SUBSCRIPTION_NOTIFICATION_DESCRIPTION, NOTIFICATION_MODE_PERSONAL
)
from notifications.tasks import sent_notification
from organizations.models import Organization, Subscription
from organizations.services.membership_services import MembershipService
from organizations.services.organization_promo_services import PromoSubscriberService
from organizations.services.organization_services import OrganizationService
from users.models import User


class SubscriptionService:
    # @classmethod
    # def is_subscribed(cls, organization: Organization, user: User) -> bool:
    #     return Subscription.objects.filter(organization=organization, user=user).exists()
    @classmethod
    def is_subscribed(cls, organization: Organization, user: User) -> str:
        try:
            subscription = Subscription.objects.get(organization=organization, user=user)
            return subscription.status
        except Subscription.DoesNotExist:
            return 'not_subscribed'

    @classmethod
    def get_number_of_subscriptions(cls, organization: Organization) -> int:
        return Subscription.objects.filter(organization=organization, status='subscribed').count()

    @classmethod
    def toggle_subscription_status(cls, organization: Organization, user: User) -> str:
        if organization.is_private is True and not OrganizationService.user_can_edit_organization(
                organization=organization, user=user) and cls.is_subscribed(organization, user) == 'not_subscribed':
            Subscription.objects.create(organization=organization, user=user, status='pending')
            return 'pending'
        elif organization.is_private is True and not OrganizationService.user_can_edit_organization(
                organization=organization, user=user) and cls.is_subscribed(organization, user) == 'pending':
            Subscription.objects.get(organization=organization, user=user, status='pending').delete()
            return 'not_subscribed'
        else:
            subscription, created = Subscription.objects.get_or_create(organization=organization, user=user)
            if created:
                PromoSubscriberService.use_promo_for_new_subscriber(organization=organization, follower=user)

                sent_notification.delay(
                    recipient_id=organization.owner_id,
                    sender_id=user.id,
                    mode=NOTIFICATION_MODE_PERSONAL,
                    notification_type=FOLLOWED_TO_ORGANIZATION_TYPE,
                    title=FOLLOWED_TO_ORGANIZATION_TITLE,
                    description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                    organization_id=organization.id,
                    extra_data=dict(address=organization.address)
                )
                sent_notification.delay(
                    recipient_id=user.id,
                    mode=NOTIFICATION_MODE_PERSONAL,
                    notification_type=ORGANIZATION_FOLLOWED_TYPE,
                    title=ORGANIZATION_FOLLOWED_TITLE.format(org_title=organization.title),
                    description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                    organization_id=organization.id,
                    extra_data=dict(org_title=organization.title, address=organization.address)
                )
                subscription.status = 'subscribed'
                subscription.save()
                return 'subscribed'

        subscription.delete()
        return False

    @classmethod
    def subscribe_to_organization(cls, organization: Organization, user: User) -> bool:
        subscription, created = Subscription.objects.get_or_create(organization=organization, user=user)
        if created:
            PromoSubscriberService.use_promo_for_new_subscriber(organization=organization, follower=user)

            sent_notification.delay(
                recipient_id=organization.owner_id,
                sender_id=user.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=FOLLOWED_TO_ORGANIZATION_TYPE,
                title=FOLLOWED_TO_ORGANIZATION_TITLE,
                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                organization_id=organization.id,
                extra_data=dict(address=organization.address)
            )

        return True

    @classmethod
    def get_user_subscriptions(cls, user: User) -> QuerySet:
        if user.is_authenticated:
            organizations = Organization.active_organizations.filter(
                id__in=user.subscriptions.values('organization_id')).annotate(
                subscription_time=Subquery(
                    Subscription.objects.filter(organization=OuterRef('pk'), user=user).values('created_at')[:1])
            ).order_by('-subscription_time')
            return organizations
        return Organization.objects.none()

    @classmethod
    def get_organization_followers(cls, organization_id: int, user: User = None) -> QuerySet:
        if user:
            organization = Organization.objects.get(id=organization_id)
            if OrganizationService.user_can_edit_organization(organization=organization, user=user):
                return User.objects.filter(subscriptions__organization_id=organization_id)
        return User.objects.filter(subscriptions__organization_id=organization_id).exclude(
            subscriptions__status='pending')

    @classmethod
    def get_follower(cls, user_id: int, organization_id: int, requested_by: User) -> User:
        organization = OrganizationService.get(id=organization_id)
        user = User.objects.get(id=user_id)
        if not MembershipService.is_organization_member_or_owner(user=requested_by, organization=organization):
            raise PermissionDeniedException(_('Permission denied'))

        if not Subscription.objects.filter(user=user, organization=organization).exists():
            raise ObjectNotFoundException(_('Follower not found'))
        return user

    @classmethod
    def get_organization_partners_followers(cls, organization_id: int) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        partners = OrganizationService.get_organization_partners(organization=organization).distinct().values('id', )
        return User.objects.filter(subscriptions__organization_id__in=partners).distinct()
