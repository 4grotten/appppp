from typing import Union

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from notifications.constants import (
    PARTNER_MODE, REQUEST_PARTNERSHIP_TYPE, PARTNERSHIP_REQUEST_TITLE,
    PARTNERSHIP_REQUEST_DESCRIPTION, REQUEST_PARTNERSHIP_RECIPIENT_TYPE, DECLINE_PARTNERSHIP_TYPE,
    DECLINE_PARTNERSHIP_RECIPIENT_TYPE, ACCEPT_PARTNERSHIP_TYPE, ACCEPT_PARTNERSHIP_RECIPIENT_TYPE)
from notifications.services import NotificationService
from notifications.tasks import (send_notifications_organization_members)
from organizations.models import Organization, Partnership
from notifications.models import Notification
from organizations.services.organization_services import OrganizationService
from users.models import User


class PartnershipService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Partnership.objects.get(*args, **kwargs)
        except Partnership.DoesNotExist:
            raise ObjectNotFoundException('Partnership not found')

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            Partnership.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException('Could not create partnership request')

    @classmethod
    def create_request(cls, user: User, requested_by: Organization, accepted_by: Organization):
        if not OrganizationService.user_can_edit_organization(organization=requested_by, user=user):
            raise NotAcceptableException('No rights to edit organization')
        cls.create(requested_by=requested_by, accepted_by=accepted_by)

        partnership = Partnership.objects.get(requested_by=requested_by, accepted_by=accepted_by)
        send_notifications_organization_members.delay(
            mode=PARTNER_MODE,
            notification_type=REQUEST_PARTNERSHIP_TYPE,
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=requested_by.title,
                                                   recipient_organization=accepted_by.title),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=requested_by.address),
            organization_id=requested_by.id,
            members_organization_id=requested_by.id,
            with_permissions=dict(can_edit_partner=True),
            extra_data=dict(parnership_id=partnership.id, should_be_deleted=True)
        )
        send_notifications_organization_members.delay(
            mode=PARTNER_MODE,
            notification_type=REQUEST_PARTNERSHIP_RECIPIENT_TYPE,
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=requested_by.title,
                                                   recipient_organization=accepted_by.title),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=requested_by.address),
            organization_id=requested_by.id,
            members_organization_id=accepted_by.id,
            with_permissions=dict(can_edit_partner=True),
            extra_data=dict(parnership_id=partnership.id, should_be_deleted=True)
        )

    @classmethod
    def are_partners(cls, requested_by: Organization, accepted_by: Organization) -> bool:
        return Partnership.objects.filter(requested_by=requested_by, accepted_by=accepted_by, is_accepted=True).exists()

    @classmethod
    def get_organization_partnerships(cls, organization: Organization, user: User) -> QuerySet:
        if not OrganizationService.user_can_edit_partner(organization=organization, user=user):
            raise NotAcceptableException('No access to partner settings')

        return Partnership.objects.filter(requested_by=organization).order_by('-is_accepted', '-id')

    @classmethod
    def get_requested_partnerships(cls, partnership_id: int, user: User) -> Union[QuerySet, None]:
        partnership = cls.get(id=partnership_id)
        try:
            return cls.get_organization_partnerships(organization=partnership.requested_by, user=user)
        except NotAcceptableException:
            return None

    @classmethod
    def delete_partnership(cls, partnership_id: int, user: User):
        partnership = cls.get(id=partnership_id)

        if not OrganizationService.user_can_edit_partner(
                organization=partnership.requested_by, user=user
        ) and not OrganizationService.user_can_edit_partner(organization=partnership.accepted_by, user=user):
            raise NotAcceptableException('No access to partner settings')

        if not partnership.is_accepted:
            # ToDo: change notification to rejected
            pass

        Notification.objects.filter(extra_data__parnership_id=partnership_id).filter(
            extra_data__should_be_deleted=True).delete()

        send_notifications_organization_members.delay(
            mode=PARTNER_MODE,
            notification_type=DECLINE_PARTNERSHIP_TYPE,
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                   recipient_organization=partnership.accepted_by.title),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
            organization_id=partnership.requested_by.id,
            members_organization_id=partnership.requested_by.id,
            with_permissions=dict(can_edit_partner=True)
        )
        send_notifications_organization_members.delay(
            mode=PARTNER_MODE,
            notification_type=DECLINE_PARTNERSHIP_RECIPIENT_TYPE,
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                   recipient_organization=partnership.accepted_by.title),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
            organization_id=partnership.requested_by.id,
            members_organization_id=partnership.accepted_by.id,
            with_permissions=dict(can_edit_partner=True)
        )

        partnership.delete()

    @classmethod
    def set_permissions(cls, partnership: Partnership, user: User,
                        can_check_attendance=False, can_see_stats=False, can_edit_organization=False) -> Partnership:
        if not OrganizationService.user_can_edit_partner(organization=partnership.accepted_by, user=user):
            raise NotAcceptableException('No access to partner settings')

        try:
            partnership.is_accepted = True
            partnership.can_check_attendance = can_check_attendance
            partnership.can_see_stats = can_see_stats
            partnership.can_edit_organization = can_edit_organization
            partnership.save()

            Notification.objects.filter(extra_data__parnership_id=partnership.id).filter(
                extra_data__should_be_deleted=True).delete()

            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                mode=PARTNER_MODE,
                notification_type=ACCEPT_PARTNERSHIP_TYPE,
                title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                       recipient_organization=partnership.accepted_by.title),
                description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
                organization_id=partnership.requested_by.id,
                members_organization_id=partnership.requested_by.id,
                with_permissions=dict(can_edit_partner=True),
                extra_data=dict(parnership_id=partnership.id)
            ))

            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                mode=PARTNER_MODE,
                notification_type=ACCEPT_PARTNERSHIP_RECIPIENT_TYPE,
                title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=partnership.requested_by.title,
                                                       recipient_organization=partnership.accepted_by.title),
                description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=partnership.requested_by.address),
                organization_id=partnership.requested_by.id,
                members_organization_id=partnership.accepted_by.id,
                with_permissions=dict(can_edit_partner=True),
                extra_data=dict(parnership_id=partnership.id)
            ))

            return partnership
        except IntegrityError:
            raise IntegrityException('Could not update partnership permissions')
