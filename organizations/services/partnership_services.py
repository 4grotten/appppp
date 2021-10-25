from typing import Union

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from common.models import Currency
from notifications.constants import (
    NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_TYPE, PARTNERSHIP_REQUEST_TITLE,
    PARTNERSHIP_REQUEST_DESCRIPTION, NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_RECIPIENT_TYPE,
    NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_TYPE,
    NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_RECIPIENT_TYPE, NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE,
    NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE, NOTIFICATION_MODE_PERSONAL
)
from notifications.models import Notification
from notifications.tasks import (send_notifications_organization_members)
from organizations.models import Organization, Partnership, CommonItemsGroup
from organizations.services.cashback_group_services import CashbackGroupService
from organizations.services.common_shop_item_services import CommonItemsGroupService
from organizations.services.cumulative_group_services import CumulativeGroupService
from organizations.services.organization_services import OrganizationService
from users.models import User


class PartnershipService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Partnership.objects.get(*args, **kwargs)
        except Partnership.DoesNotExist:
            raise ObjectNotFoundException(_('Partnership not found'))

    @classmethod
    def create(cls, *args, **kwargs) -> Partnership:
        try:
            return Partnership.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException(_('Could not create partnership request'))

    @classmethod
    def create_request(cls, user: User, requested_by: Organization, accepted_by: Organization,
                       partnership_id: int):

        if partnership_id:
            accepted_partner = cls.get(id=partnership_id)
            requested_by = requested_by or accepted_partner.accepted_by
            accepted_by = accepted_by or accepted_partner.requested_by

        if not OrganizationService.user_can_edit_organization(organization=requested_by, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        partnership = cls.create(requested_by=requested_by, accepted_by=accepted_by)

        if partnership_id:
            partner = cls.get(id=partnership_id)
            partner.is_accepted = True
            partner.save()
            partnership.is_accepted = True
            partnership.save()

            #  # TODO check logic of this block sanding notification
            '''Delete request partnerships notification'''
            transaction.on_commit(
                lambda: Notification.objects.filter(extra_data__partnership_id=accepted_partner.id).filter(
                    extra_data__should_be_deleted=True).delete())

            '''Send accept partnership notification'''
            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                mode=NOTIFICATION_MODE_PERSONAL,
                sender_id=user.id,
                notification_type=NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE,
                title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=accepted_partner.requested_by.title,
                                                       recipient_organization=accepted_partner.accepted_by.title),
                description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=accepted_partner.requested_by.address),
                organization_id=accepted_partner.requested_by.id,
                members_organization_id=accepted_partner.requested_by.id,
                with_permissions=dict(can_edit_partner=True),
                extra_data=dict(partnership_id=partnership.id,
                                sender_organization=accepted_partner.requested_by.title,
                                recipient_organization=accepted_partner.accepted_by.title,
                                address=accepted_partner.requested_by.address)
            ))

            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                mode=NOTIFICATION_MODE_PERSONAL,
                sender_id=user.id,
                notification_type=NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE,
                title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=accepted_partner.requested_by.title,
                                                       recipient_organization=accepted_partner.accepted_by.title),
                description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=accepted_partner.requested_by.address),
                organization_id=accepted_partner.requested_by.id,
                members_organization_id=accepted_partner.accepted_by.id,
                with_permissions=dict(can_edit_partner=True),
                extra_data=dict(partnership_id=accepted_partner.id,
                                sender_organization=accepted_partner.requested_by.title,
                                recipient_organization=accepted_partner.accepted_by.title,
                                address=accepted_partner.requested_by.address)
            ))

        '''Send request partnership notification'''
        if not partnership_id:
            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                mode=NOTIFICATION_MODE_PERSONAL,
                sender_id=user.id,
                notification_type=NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_TYPE,
                title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=requested_by.title,
                                                       recipient_organization=accepted_by.title),
                description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=requested_by.address),
                organization_id=requested_by.id,
                members_organization_id=requested_by.id,
                with_permissions=dict(can_edit_partner=True),
                extra_data=dict(partnership_id=partnership.id, should_be_deleted=True,
                                sender_organization=requested_by.title,
                                recipient_organization=accepted_by.title, address=requested_by.address)
            ))
            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_RECIPIENT_TYPE,
                title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=requested_by.title,
                                                       recipient_organization=accepted_by.title),
                description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=requested_by.address),
                organization_id=requested_by.id,
                members_organization_id=accepted_by.id,
                with_permissions=dict(can_edit_partner=True),
                extra_data=dict(partnership_id=partnership.id, should_be_deleted=True,
                                sender_organization=requested_by.title,
                                recipient_organization=accepted_by.title, address=requested_by.address)
            ))

    @classmethod
    def are_partners(cls, requested_by: Organization, accepted_by: Organization) -> bool:
        return Partnership.objects.filter(requested_by=requested_by, accepted_by=accepted_by, is_accepted=True).exists()

    @classmethod
    def get_organization_partnerships_by_user(cls, organization: Organization, user: User) -> QuerySet:
        if not OrganizationService.user_can_edit_partner(organization=organization, user=user):
            raise NotAcceptableException(_('No access to partner settings'))

        partnerships = Partnership.objects.filter(
            (Q(accepted_by=organization) & Q(requested_by__is_deleted=False))
            | (Q(requested_by=organization) & Q(is_accepted=False) & Q(accepted_by__is_deleted=False))
        ).order_by('is_accepted', '-id')
        return partnerships

    @classmethod
    def get_organization_partners(cls, organization: Organization) -> QuerySet:
        return OrganizationService.get_organization_partners(organization)

    @classmethod
    def get_organization_partnerships_for_mass_subscription(cls, organization: Organization) -> QuerySet:
        partnerships = Partnership.objects.filter(
            (Q(accepted_by=organization) & Q(requested_by__is_deleted=False))
            | (Q(requested_by=organization) & Q(is_accepted=False) & Q(accepted_by__is_deleted=False))
        ).order_by('is_accepted', '-id')
        return partnerships

    @classmethod
    def get_incoming_partnerships(cls, partnership_id: int, user: User) -> Union[QuerySet, None]:
        partnership = cls.get(id=partnership_id)

        if not OrganizationService.user_can_edit_partner(organization=partnership.accepted_by, user=user):
            raise NotAcceptableException(_('No access to partner settings'))

        try:
            return Partnership.objects.filter(accepted_by=partnership.accepted_by).filter(id=partnership_id)
        except NotAcceptableException:
            return None

    @classmethod
    def delete_partnership(cls, partnership_id: int, user: User):
        partnership = cls.get(id=partnership_id)
        if not OrganizationService.user_can_edit_partner(
                organization=partnership.requested_by, user=user
        ) and not OrganizationService.user_can_edit_partner(organization=partnership.accepted_by, user=user):
            raise NotAcceptableException(_('No access to partner settings'))

        transaction.on_commit(lambda: Notification.objects.filter(extra_data__partnership_id=partnership_id).filter(
            extra_data__should_be_deleted=True).delete())

        transaction.on_commit(lambda: send_notifications_organization_members.delay(
            mode=NOTIFICATION_MODE_PERSONAL,
            sender_id=user.id,
            notification_type=NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_TYPE,
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                   recipient_organization=partnership.accepted_by.title),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
            organization_id=partnership.requested_by.id,
            members_organization_id=partnership.requested_by.id,
            with_permissions=dict(can_edit_partner=True),
            extra_data=dict(sender_organization=partnership.requested_by.title,
                            recipient_organization=partnership.accepted_by.title,
                            address=partnership.requested_by.address),
        ))
        transaction.on_commit(lambda: send_notifications_organization_members.delay(
            mode=NOTIFICATION_MODE_PERSONAL,
            sender_id=user.id,
            notification_type=NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_RECIPIENT_TYPE,
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                   recipient_organization=partnership.accepted_by.title),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
            organization_id=partnership.requested_by.id,
            members_organization_id=partnership.accepted_by.id,
            with_permissions=dict(can_edit_partner=True),
            extra_data=dict(sender_organization=partnership.requested_by.title,
                            recipient_organization=partnership.accepted_by.title,
                            address=partnership.requested_by.address),
        ))

        # # TODO пересмотреть флоу
        try:
            common_shop_group = CommonItemsGroup.objects.get(organizations=partnership.accepted_by)
            partnership.accepted_by.items_group = None
            partnership.accepted_by.save(update_fields=('items_group',))
            count_org_in_common_group = common_shop_group.organizations.count()
            if count_org_in_common_group == 1:
                partnership.requested_by.items_group = None
                partnership.requested_by.save(update_fields=('items_group',))
                common_shop_group.delete()
        except ObjectDoesNotExist:
            pass
        try:
            Partnership.objects.get(accepted_by=partnership.requested_by, requested_by=partnership.accepted_by).delete()
        except Partnership.DoesNotExist:
            pass
        partnership.delete()

    @classmethod
    @transaction.atomic
    def set_permissions(cls, partnership: Partnership, user: User,
                        can_check_attendance: bool = False, can_see_stats: bool = False,
                        can_edit_organization: bool = False, can_share_cashback: bool = False,
                        can_share_cumulative: bool = False, can_share_items: bool = False) -> Partnership:
        if not OrganizationService.user_can_edit_partner(organization=partnership.accepted_by, user=user):
            raise NotAcceptableException(_('No access to partner settings'))

        is_new_request = not partnership.is_accepted
        is_sharing_cashback = can_share_cashback and not partnership.can_share_cashback
        is_sharing_cumulative = can_share_cumulative and not partnership.can_share_cumulative
        is_sharing_items = can_share_items and not partnership.can_share_items

        # # TODO пересмотреть флоу
        if can_share_items is False:
            try:
                partnership.is_accepted = True
                common_shop_group = CommonItemsGroup.objects.get(organizations=partnership.accepted_by)
                partnership.accepted_by.items_group = None
                partnership.accepted_by.save(update_fields=('items_group',))
                count_org_in_common_group = common_shop_group.organizations.count()
                if count_org_in_common_group < 1:
                    common_shop_group.delete()
            except ObjectDoesNotExist:
                pass

        if is_sharing_items or is_sharing_cumulative or is_sharing_cashback:
            if not partnership.requested_by.currency == partnership.accepted_by.currency:
                raise NotAcceptableException(_('Should have same currency to have shared discounts and items'))

        try:
            partnership.can_check_attendance = can_check_attendance
            partnership.can_see_stats = can_see_stats
            partnership.can_edit_organization = can_edit_organization
            partnership.can_share_cashback = can_share_cashback
            partnership.can_share_cumulative = can_share_cumulative
            partnership.can_share_items = can_share_items
            partnership.save()

            if is_sharing_cashback:
                cls.check_and_create_mutual_cashback(one_way_partnership=partnership)

            if is_sharing_cumulative:
                cls.check_and_create_shared_cumulative(one_way_partnership=partnership)

            if is_sharing_items:
                cls.check_and_create_common_items(one_way_partnership=partnership)

            if is_new_request:
                reverse_partnership = cls.create(requested_by=partnership.accepted_by,
                                                 accepted_by=partnership.requested_by, is_accepted=True)

                transaction.on_commit(
                    lambda: Notification.objects.filter(extra_data__partnership_id=partnership.id).filter(
                        extra_data__should_be_deleted=True).delete())

                transaction.on_commit(lambda: send_notifications_organization_members.delay(
                    mode=NOTIFICATION_MODE_PERSONAL,
                    sender_id=user.id,
                    notification_type=NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE,
                    title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                           recipient_organization=partnership.accepted_by.title),
                    description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
                    organization_id=partnership.requested_by.id,
                    members_organization_id=partnership.requested_by.id,
                    with_permissions=dict(can_edit_partner=True),
                    extra_data=dict(partnership_id=reverse_partnership.id,
                                    sender_organization=partnership.requested_by.title,
                                    recipient_organization=partnership.accepted_by.title,
                                    address=partnership.requested_by.address)
                ))

                transaction.on_commit(lambda: send_notifications_organization_members.delay(
                    mode=NOTIFICATION_MODE_PERSONAL,
                    sender_id=user.id,
                    notification_type=NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE,
                    title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                           recipient_organization=partnership.accepted_by.title),
                    description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
                    organization_id=partnership.requested_by.id,
                    members_organization_id=partnership.accepted_by.id,
                    with_permissions=dict(can_edit_partner=True),
                    extra_data=dict(partnership_id=partnership.id, sender_organization=partnership.requested_by.title,
                                    recipient_organization=partnership.accepted_by.title,
                                    address=partnership.requested_by.address)
                ))

            return partnership
        except IntegrityError:
            raise IntegrityException(_('Could not update partnership permissions'))

    @classmethod
    def check_and_create_mutual_cashback(cls, one_way_partnership: Partnership):
        reverse_partnership = Partnership.objects.filter(
            requested_by=one_way_partnership.accepted_by,
            accepted_by=one_way_partnership.requested_by,
            is_accepted=True, can_share_cashback=True
        ).first()

        if reverse_partnership is None:
            return

        CashbackGroupService.link_organizations_in_cashback_group(first=one_way_partnership.accepted_by,
                                                                  second=one_way_partnership.requested_by)

    @classmethod
    def check_and_create_shared_cumulative(cls, one_way_partnership: Partnership):
        reverse_partnership = Partnership.objects.filter(
            requested_by=one_way_partnership.accepted_by,
            accepted_by=one_way_partnership.requested_by,
            is_accepted=True, can_share_cumulative=True
        ).first()

        if reverse_partnership is None:
            return

        CumulativeGroupService.link_organizations_in_cumulative_group(first=one_way_partnership.accepted_by,
                                                                      second=one_way_partnership.requested_by)

    @classmethod
    def check_and_create_common_items(cls, one_way_partnership: Partnership):
        reverse_partnership = Partnership.objects.filter(
            requested_by=one_way_partnership.accepted_by,
            accepted_by=one_way_partnership.requested_by,
            is_accepted=True, can_share_items=True
        ).first()

        if reverse_partnership is None:
            return

        CommonItemsGroupService.link_organizations_with_common_items_group(first=one_way_partnership.accepted_by,
                                                                           second=one_way_partnership.requested_by)

    @classmethod
    def can_change_currency(cls, organization: Organization, currency: Currency):
        currency_partnerships = Partnership.objects.filter(
            is_accepted=True, can_share_cashback=True, can_share_cumulative=True, can_share_items=True
        )
        different_currency_requesting_partners_exist = currency_partnerships.filter(
            accepted_by=organization, requested_by__is_deleted=False
        ).exclude(requested_by__currency=currency).exists()
        different_currency_accepting_partners = currency_partnerships.filter(
            requested_by=organization, accepted_by__is_deleted=False
        ).exclude(accepted_by__currency=currency).exists()

        return not (different_currency_requesting_partners_exist | different_currency_accepting_partners)
