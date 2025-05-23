from decimal import Decimal
from typing import Optional
from django.db import transaction as db_transaction
from django.db.models import QuerySet, F, Q
from django.db.models import Subquery, OuterRef
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from django.utils.timezone import now

from common.exceptions import PermissionDeniedException, ObjectNotFoundException, NotAcceptableException
from common.models import Currency
from common.services.currency import CurrencyConverterService
from notifications.constants import (
    FOLLOWED_TO_ORGANIZATION_TYPE,
    FOLLOWED_TO_ORGANIZATION_TITLE, ORGANIZATION_FOLLOWED_TYPE,
    ORGANIZATION_FOLLOWED_TITLE, SUBSCRIPTION_NOTIFICATION_DESCRIPTION, NOTIFICATION_MODE_PERSONAL,
    BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION, BG_ORGANIZATION_FOLLOWED_DESCRIPTION,
    BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_RU, BG_ORGANIZATION_FOLLOWED_DESCRIPTION_RU,
    BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_DE, BG_ORGANIZATION_FOLLOWED_DESCRIPTION_DE,
    BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_TR, BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_ZH,
    BG_ORGANIZATION_FOLLOWED_DESCRIPTION_TR, BG_ORGANIZATION_FOLLOWED_DESCRIPTION_ZH
)
from notifications.tasks import sent_notification
from organizations.models import Organization, Subscription, BlockedUser, RegionalTariff, UserOrgSubscription
from organizations.services.membership_services import MembershipService
from organizations.services.organization_promo_services import PromoSubscriberService
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from users.models import User, PromoCode, ReferralTransaction, ReferralBalance
from users.services import UserService


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
                from users.serializers import UserInfoSerializer
                sent_notification.delay(
                    recipient_id=organization.owner_id,
                    sender_id=user.id,
                    mode=NOTIFICATION_MODE_PERSONAL,
                    notification_type=FOLLOWED_TO_ORGANIZATION_TYPE,
                    title=FOLLOWED_TO_ORGANIZATION_TITLE,
                    description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                    organization_id=organization.id,
                    extra_data=dict(address=organization.address,
                                    bg_description=BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION,
                                    bg_description_ru=BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_RU,
                                    bg_description_de=BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_DE,
                                    bg_description_tr=BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_TR,
                                    bg_description_zh=BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_ZH,
                                    sender=UserInfoSerializer(user).data)
                )
                sent_notification.delay(
                    recipient_id=user.id,
                    mode=NOTIFICATION_MODE_PERSONAL,
                    notification_type=ORGANIZATION_FOLLOWED_TYPE,
                    title=ORGANIZATION_FOLLOWED_TITLE.format(org_title=organization.title),
                    description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                    organization_id=organization.id,
                    extra_data=dict(org_title=organization.title,
                                    address=organization.address,
                                    bg_description_client=BG_ORGANIZATION_FOLLOWED_DESCRIPTION,
                                    bg_description_client_ru=BG_ORGANIZATION_FOLLOWED_DESCRIPTION_RU,
                                    bg_description_client_de=BG_ORGANIZATION_FOLLOWED_DESCRIPTION_DE,
                                    bg_description_client_tr=BG_ORGANIZATION_FOLLOWED_DESCRIPTION_TR,
                                    bg_description_client_zh=BG_ORGANIZATION_FOLLOWED_DESCRIPTION_ZH)
                )
                subscription.status = 'subscribed'
                subscription.save()
                return 'subscribed'

        subscription.delete()
        return 'not_subscribed'

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
        organization = Organization.objects.get(id=organization_id)
        if organization.show_followers:
            if user:
                if OrganizationService.user_can_edit_organization(organization=organization, user=user):
                    return User.objects.filter(subscriptions__organization_id=organization_id).order_by(
                        '-subscriptions__id')
                return User.objects.filter(
                    Q(subscriptions__organization=organization) & Q(subscriptions__status='subscribed')).order_by(
                    '-subscriptions__id')
            return User.objects.filter(
                Q(subscriptions__organization=organization) & Q(subscriptions__status='subscribed')).order_by(
                '-subscriptions__id')
        else:
            if user:
                if OrganizationService.user_can_edit_organization(organization=organization, user=user) and \
                        OrganizationService.user_can_see_stats(organization=organization, user=user):
                    return User.objects.filter(subscriptions__organization_id=organization_id).order_by(
                        '-subscriptions__id')

            raise PermissionDeniedException(_('No rights to get followers'))

    @classmethod
    def get_organization_blocked_users(cls, organization_id: int, user: User) -> QuerySet:
        organization = Organization.objects.get(id=organization_id)
        if OrganizationService.user_can_edit_organization(organization=organization, user=user):
            return User.objects.filter(blocked_user__organization_id=organization_id).order_by('-blocked_user__id')

        raise PermissionDeniedException(_('No rights to get blocked users'))

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
    def get_blocked_user(cls, user_id: int, organization_id: int, requested_by: User) -> User:
        organization = OrganizationService.get(id=organization_id)
        user = UserService.get(id=user_id)
        if not OrganizationService.user_can_edit_organization(user=requested_by, organization=organization):
            raise PermissionDeniedException(_('Permission denied'))

        if not BlockedUser.objects.filter(user=user, organization=organization).exists():
            raise ObjectNotFoundException(_('Blocked user not found'))
        return user

    @classmethod
    def get_organization_partners_followers(cls, organization_id: int) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        partners = OrganizationService.get_organization_partners(organization=organization).distinct().values('id', )
        return User.objects.filter(subscriptions__organization_id__in=partners).distinct()

    @classmethod
    def accept_follower(cls, organization: Organization, user: User):
        Subscription.objects.filter(organization=organization, user=user, status='pending').update(
            status='subscribed')

    @classmethod
    def refuse_follower(cls, organization: int, user: int):
        Subscription.objects.filter(organization=organization, user=user).delete()

    @classmethod
    def accept_all_followers(cls, organization: Organization):
        subscriptions = Subscription.objects.filter(organization=organization, status='pending')

        for i in subscriptions:
            PromoSubscriberService.use_promo_for_new_subscriber(
                organization=organization,
                follower=i.user)

            sent_notification.delay(
                recipient_id=organization.owner_id,
                sender_id=i.user.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=FOLLOWED_TO_ORGANIZATION_TYPE,
                title=FOLLOWED_TO_ORGANIZATION_TITLE,
                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                organization_id=organization.id,
                extra_data=dict(address=organization.address)
            )
            sent_notification.delay(
                recipient_id=i.user.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=ORGANIZATION_FOLLOWED_TYPE,
                title=ORGANIZATION_FOLLOWED_TITLE.format(org_title=organization.title),
                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=organization.address),
                organization_id=organization.id,
                extra_data=dict(org_title=organization.title, address=organization.address)
            )

            cls.accept_follower(organization=organization, user=i.user)


class UserOrgSubscriptionService:

    @classmethod
    def create_user_org_subscription(cls, user: User, processed_by: User, organization: Organization,
                                     tariff: RegionalTariff, utc_offset_minutes: int,
                                     promocode: Optional[PromoCode] = None):
        total_price = tariff.total_price
        discount_percent = Decimal(promocode.discount_percent) if promocode else Decimal('0')
        profit_percent = Decimal(promocode.profit_percent) if promocode else Decimal('0')
        final_price = total_price * (Decimal('1') - discount_percent / Decimal('100'))

        with db_transaction.atomic():
            transaction = cls.create_user_org_subscription_transaction(
                user=user,
                processed_by=processed_by,
                organization=organization,
                tariff=tariff,
                utc_offset_minutes=utc_offset_minutes,
                final_price=final_price
            )

            subscription = UserOrgSubscription.objects.create(
                user=user,
                organization=organization,
                transaction=transaction,
                tariff=tariff,
            )

            if promocode:
                profit_amount = total_price * (profit_percent / Decimal('100'))
                currency = tariff.country.currency

                profit_usdt = CurrencyConverterService.convert(from_currency=transaction.currency.code,
                                                                    to_currency="USD", amount=profit_amount)
                # Создание записи в истории
                ReferralTransaction.objects.create(
                    promocode=promocode,
                    owner=promocode.owner,
                    referred_user=user,
                    subscription=subscription,
                    profit_amount_usdt=profit_usdt,
                    original_currency=currency,
                    original_amount=profit_amount
                )

                # Обновление баланса
                balance, _ = ReferralBalance.objects.get_or_create(user=promocode.owner)
                balance.total_earned += profit_usdt
                balance.current_balance += profit_usdt
                balance.save(update_fields=["total_earned", "current_balance"])

        return subscription

    @classmethod
    def create_user_org_subscription_transaction(cls, user: User, processed_by: User, tariff: RegionalTariff,
                                                 organization: Organization, utc_offset_minutes: int,
                                                 final_price):
        currency = tariff.country.currency
        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)

        transaction = Transaction.objects.create(
            client=user,
            processed_by=processed_by,
            employee_role=role,
            employee_name=processed_by.full_name,
            employee_avatar=processed_by.avatar,
            organization=organization,
            type=Transaction.ORG_SUBSCRIPTION,
            delivery_type=Transaction.ONLINE_PAYMENT,
            original_amount=final_price,
            currency=currency,
            status=Transaction.ACCEPTED,
            payment_status=Transaction.IN_PROGRESS,
            display_time=now() + timedelta(minutes=utc_offset_minutes)
        )
        transaction.save()

        return transaction
