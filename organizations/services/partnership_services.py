from typing import Union

from django.db import IntegrityError
from django.db.models import QuerySet

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from notifications.constants import (
    PARTNER_MODE, REQUEST_PARTNERSHIP_TYPE, PARTNERSHIP_REQUEST_TITLE,
    PARTNERSHIP_REQUEST_DESCRIPTION)
from notifications.services import NotificationService
from notifications.tasks import send_notifications_to_all_users, sent_notification
from organizations.models import Organization, Partnership
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

        # sent_notification.delay(
        #     recipient_id=requested_by.owner_id,
        #     mode=PARTNER_MODE,
        #     notification_type=REQUEST_PARTNERSHIP_TYPE,
        #     title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=requested_by.title,
        #                                            recipient_organization=accepted_by.title),
        #     description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=requested_by.address),
        #     organization_id=requested_by.id,
        #     extra_data=dict(parnership_id=partnership.id)
        # )

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

        partnership.delete()

    @classmethod
    def set_permissions(cls, partnership: Partnership, user: User,
                        can_check_attendance: bool, can_see_stats: bool, can_edit_organization: bool) -> Partnership:
        if not OrganizationService.user_can_edit_partner(organization=partnership.accepted_by, user=user):
            raise NotAcceptableException('No access to partner settings')

        try:
            partnership.is_accepted = True
            partnership.can_check_attendance = can_check_attendance
            partnership.can_see_stats = can_see_stats
            partnership.can_edit_organization = can_edit_organization
            partnership.save()
            return partnership
        except IntegrityError:
            raise IntegrityException('Could not update partnership permissions')
