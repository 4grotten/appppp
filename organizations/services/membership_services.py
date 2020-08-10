from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from common.exceptions import ObjectNotFoundException, NotAcceptableException, IntegrityException
from notifications.constants import (PARTNER_MODE, RECRUIT_JOB_TYPE, RECRUIT_JOB_TITLE, RECRUIT_JOB_DESCRIPTION,
                                     PERSONAL_MODE, CHANGE_JOB_POSITION_TYPE, CHANGE_JOB_POSITION_TITLE,
                                     CHANGE_JOB_POSITION_DESCRIPTION, DISMISS_JOB_TYPE, DISMISS_JOB_TITLE,
                                     DISMISS_JOB_DESCRIPTION)
from organizations.models import Membership, Organization, Role
from notifications.tasks import sent_notification
from users.models import User


class MembershipService:
    @classmethod
    def get(cls, *args, **kwargs) -> Membership:
        try:
            return Membership.objects.get(*args, **kwargs)
        except Membership.DoesNotExist:
            raise ObjectNotFoundException('Membership not found')

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            membership = Membership.objects.create(*args, **kwargs)

            transaction.on_commit(lambda: sent_notification.delay(
                recipient_id=membership.user_id,
                sender_id=membership.added_by_id,
                mode=PERSONAL_MODE,
                notification_type=RECRUIT_JOB_TYPE,
                title=RECRUIT_JOB_TITLE,
                description=RECRUIT_JOB_DESCRIPTION.format(position=membership.role.title),
                organization_id=membership.organization_id
            ))

        except IntegrityError:
            raise IntegrityException('Could not add employee')

    @classmethod
    def get_organization_employees(cls, organization: Organization) -> QuerySet:
        return Membership.objects.filter(organization=organization).order_by('role')

    @classmethod
    def dismiss_employee(cls, membership: Membership):

        transaction.on_commit(lambda: sent_notification.delay(
            recipient_id=membership.user_id,
            sender_id=membership.added_by_id,
            mode=PERSONAL_MODE,
            notification_type=DISMISS_JOB_TYPE,
            title=DISMISS_JOB_TITLE,
            description=DISMISS_JOB_DESCRIPTION.format(position=membership.role.title),
            organization_id=membership.organization_id
        ))
        return membership.delete()

    @classmethod
    def add_employee(cls, organization: Organization, employee: User, role: Role, added_by: User) -> Membership:
        from organizations.services.organization_services import OrganizationService

        if employee == organization.owner:
            raise NotAcceptableException('Insufficient rights')

        if not role.organization == organization:
            raise NotAcceptableException('No such role in organization')

        if not OrganizationService.user_can_edit_organization(organization=organization, user=added_by):
            raise NotAcceptableException('No rights to edit organization')

        return cls.create(organization=organization, user=employee, role=role, added_by=added_by)

    @classmethod
    def update_role(cls, membership: Membership, new_role: Role) -> Membership:
        if not new_role.organization == membership.organization:
            raise NotAcceptableException('No such role in organization')
        try:
            old_position = membership.role
            membership.role = new_role
            membership.save()
            transaction.on_commit(lambda: sent_notification.delay(
                recipient_id=membership.user_id,
                sender_id=membership.added_by_id,
                mode=PERSONAL_MODE,
                notification_type=CHANGE_JOB_POSITION_TYPE,
                title=CHANGE_JOB_POSITION_TITLE,
                description=CHANGE_JOB_POSITION_DESCRIPTION.format(old_position=old_position.title,
                                                                   new_position=new_role.title),
                organization_id=membership.organization_id
            ))
            return membership
        except IntegrityError:
            raise IntegrityException('Could not update role')

    @classmethod
    def has_edit_rights_in_any_organization(cls, user: User) -> bool:
        return Membership.objects.filter(user=user, role__can_edit_organization=True).exists()


class RoleService:
    @classmethod
    def get(cls, *args, **kwargs) -> Membership:
        try:
            return Role.objects.get(*args, **kwargs)
        except Role.DoesNotExist:
            raise ObjectNotFoundException('Role not found')

    @classmethod
    def filter(cls, *args, **kwargs):
        return Role.objects.filter(*args, **kwargs)
