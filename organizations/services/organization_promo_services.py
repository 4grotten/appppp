from decimal import Decimal
from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import F, QuerySet, Q
from django.utils.translation import gettext_lazy as _

from common.exceptions import (
    NotAcceptableException, IntegrityException, ObjectNotFoundException, PermissionDeniedException
)
from common.models import File
from organizations.models import Organization, OrganizationPromo, PromoEditLog, PromoSubscriber, OrganizationType
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from users.models import User


class OrganizationPromoService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return OrganizationPromo.objects.get(*args, **kwargs)
        except OrganizationPromo.DoesNotExist:
            raise ObjectNotFoundException(_('Organization promo not found'))

    @classmethod
    def filter(cls, *args, **kwargs):
        return OrganizationPromo.objects.filter(*args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            return OrganizationPromo.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException(_('Could not save organization promo'))

    @classmethod
    def get_promo_for_user(cls, organization_id: int, user: User) -> Optional[OrganizationPromo]:
        organization = OrganizationService.get(id=organization_id)
        if not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise PermissionDeniedException(_('No rights to get promo details'))

        promo = getattr(organization, 'promo', None)
        if promo is None:
            raise ObjectNotFoundException(_('Organization does not have promo'))
        return promo

    @classmethod
    def get_promo_stats_for_user(cls, organization_id: int, user: User) -> dict:
        organization = OrganizationService.get(id=organization_id)
        if not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise PermissionDeniedException(_('No rights to get promo details'))
        return {
            'subscribers_count': organization.promo_subscribers.count()
        }

    @classmethod
    @transaction.atomic
    def create_organization_promo(cls, user: User, organization: Organization, total_cashback: Decimal,
                                  cashback: Decimal, image: File) -> OrganizationPromo:
        if not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        promo = cls.create(organization=organization, total_cashback=total_cashback, cashback=cashback, image=image)
        PromoEditLogService.record_action(promo=promo, changed_by=user)
        DiscountCardService.create_zero_cashback_card(organization=organization)
        return promo

    @classmethod
    @transaction.atomic
    def update_organization_promo(cls, organization_promo: OrganizationPromo, total_cashback: Decimal,
                                  cashback: Decimal, image: File, changed_by: User):
        try:
            organization_promo.total_cashback = organization_promo.granted_amount + total_cashback
            organization_promo.cashback = cashback
            organization_promo.image = image
            organization_promo.save()
            PromoEditLogService.record_action(promo=organization_promo, changed_by=changed_by)
            return organization_promo
        except Exception as e:
            raise IntegrityException(_('Can not update organization_promo: {}').format(str(e)))

    @classmethod
    def get_usable_promo(cls, organization: Organization) -> Optional[OrganizationPromo]:
        promo = getattr(organization, 'promo', None)
        if promo is None:
            return None
        if promo.total_cashback - promo.granted_amount >= promo.cashback:
            return promo
        return None

    @classmethod
    def get_available_promo_cashback_amount(cls, organization: Organization) -> Optional[Decimal]:
        promo = cls.get_usable_promo(organization=organization)
        if promo is None:
            return None
        return promo.cashback

    @classmethod
    def get_active_promos(cls) -> QuerySet:
        return OrganizationPromo.objects.filter(cashback__lte=F('total_cashback') - F('granted_amount')).exclude(
            Q(organization__is_active=False) | Q(organization__is_deleted=True) | Q(organization__is_banned=True))

    @classmethod
    def get_types_with_active_promos(cls, country: Optional[str] = None) -> QuerySet:
        active_promos_query = cls.get_active_promos()

        if country:
            active_promos_query = active_promos_query.filter(organization__country__code=country)

        organization_ids = active_promos_query.values_list('organization_id', flat=True)

        return OrganizationType.objects.filter(
            organizations__id__in=organization_ids
        ).distinct().order_by('title')

    @classmethod
    def get_filtering_promos_by_country(cls, country: Optional[str] = None,
                                        type_id: Optional[int] = None) -> QuerySet:
        query = cls.get_active_promos()
        if country:
            query = query.filter(organization__country__code=country)

        if type_id:
            query = query.filter(organization__types__id=type_id)

        return query.distinct()


class PromoEditLogService:
    @classmethod
    def create(cls, *args, **kwargs):
        try:
            PromoEditLog.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException(_('Could not save promo edit log'))

    @classmethod
    def record_action(cls, promo: OrganizationPromo, changed_by: User):
        role = OrganizationService.get_user_role_in_organization(organization=promo.organization, user=changed_by)
        cls.create(promo=promo, changed_by=changed_by, employee_name=changed_by.full_name,
                   employee_role=role, employee_avatar=changed_by.avatar)


class PromoSubscriberService:
    @classmethod
    @transaction.atomic
    def use_promo_for_new_subscriber(cls, organization: Organization, follower: User):
        promo = OrganizationPromoService.get_usable_promo(organization=organization)
        if promo is None:
            return
        try:
            PromoSubscriber.objects.create(organization=organization, subscriber=follower, cashback=promo.cashback)
            promo.granted_amount = F('granted_amount') + promo.cashback
            promo.save()
            promo.refresh_from_db()
            OrganizationClientFinancialStatusService.change_accrued_cashback(user=follower, organization=organization,
                                                                             change_amount=promo.cashback)
        except IntegrityError:
            return

    @classmethod
    def user_has_promo_cashback(cls, organization: Organization, user: User):
        return PromoSubscriber.objects.filter(organization=organization, subscriber=user).exists()
