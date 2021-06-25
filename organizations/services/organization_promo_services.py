from decimal import Decimal
from typing import Optional

from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _

from common.exceptions import (
    NotAcceptableException, IntegrityException, ObjectNotFoundException, PermissionDeniedException
)
from common.models import File
from organizations.models import Organization, OrganizationPromo, PromoEditLog
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
        return promo

    @classmethod
    @transaction.atomic
    def update_organization_promo(cls, organization_promo: OrganizationPromo, total_cashback: Decimal,
                                  cashback: Decimal, image: File, changed_by: User):
        try:
            # ToDo: add check logic
            organization_promo.total_cashback = total_cashback
            organization_promo.cashback = cashback
            organization_promo.image = image
            organization_promo.save()
            PromoEditLogService.record_action(promo=organization_promo, changed_by=changed_by)
            return organization_promo
        except Exception as e:
            raise IntegrityException(_('Can not update organization_promo: {}').format(str(e)))


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
