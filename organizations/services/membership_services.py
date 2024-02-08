from django.db import IntegrityError, transaction
from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException, NotAcceptableException, IntegrityException
from notifications.constants import (
    NOTIFICATION_TYPE_RECRUIT_JOB_TYPE, RECRUIT_JOB_TITLE, RECRUIT_JOB_DESCRIPTION, NOTIFICATION_MODE_PERSONAL, NOTIFICATION_TYPE_CHANGE_JOB_POSITION,
    CHANGE_JOB_POSITION_TITLE, CHANGE_JOB_POSITION_DESCRIPTION, QUIT_JOB_TITLE, QUIT_JOB_DESCRIPTION,
    NOTIFICATION_TYPE_QUIT_JOB, DISMISS_JOB_TITLE, NOTIFICATION_TYPE_DISMISS_JOB, DISMISS_JOB_DESCRIPTION, NOTIFICATION_TYPE_GET_JOB_TYPE, GET_JOB_TITLE,
    GET_JOB_DESCRIPTION, NOTIFICATION_TYPE_CHANGE_JOB_POSITION_OWNER, CHANGE_JOB_POSITION_OWNER_TITLE,
    CHANGE_JOB_POSITION_OWNER_DESCRIPTION
)
from notifications.tasks import sent_notification, send_notifications_organization_members
from organizations.models import Membership, Organization, Role
from users.models import User


class MembershipService:
    @classmethod
    def get(cls, *args, **kwargs) -> Membership:
        try:
            return Membership.objects.get(*args, **kwargs)
        except Membership.DoesNotExist:
            raise ObjectNotFoundException(_('Membership not found'))

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            membership = Membership.objects.create(*args, **kwargs)
            send_notifications_organization_members.delay(
                with_permissions=dict(can_edit_organization=True),
                exclusion=[membership.user_id],
                members_organization_id=membership.organization_id,
                sender_id=membership.user_id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NOTIFICATION_TYPE_RECRUIT_JOB_TYPE,
                title=RECRUIT_JOB_TITLE,
                description=RECRUIT_JOB_DESCRIPTION.format(position=membership.role.title),
                organization_id=membership.organization_id,
                extra_data=dict(membership_id=membership.id,
                                can_edit_organization=True,
                                position=membership.role.title)
            )
            sent_notification.delay(
                recipient_id=membership.user_id,
                sender_id=membership.added_by_id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NOTIFICATION_TYPE_GET_JOB_TYPE,
                title=GET_JOB_TITLE.format(organization=membership.organization.title),
                description=GET_JOB_DESCRIPTION.format(position=membership.role.title),
                organization_id=membership.organization_id,
                extra_data=dict(membership_id=membership.id, organization=membership.organization.title,
                                position=membership.role.title,
                                can_edit_organization=membership.role.can_edit_organization)
            )
            return membership
        except IntegrityError:
            raise IntegrityException(_('Could not add employee'))

    @classmethod
    def get_organization_employees(cls, organization: Organization) -> QuerySet:
        return Membership.objects.filter(organization=organization).order_by('role')

    @classmethod
    def dismiss_employee(cls, membership: Membership):

        transaction.on_commit(lambda: sent_notification.delay(
            recipient_id=membership.user_id,
            sender_id=membership.added_by_id,
            mode=NOTIFICATION_MODE_PERSONAL,
            notification_type=NOTIFICATION_TYPE_QUIT_JOB,
            title=QUIT_JOB_TITLE.format(organization=membership.organization.title),
            description=QUIT_JOB_DESCRIPTION.format(position=membership.role.title),
            organization_id=membership.organization_id,
            extra_data=dict(organization=membership.organization.title, position=membership.role.title)
        ))
        transaction.on_commit(lambda: send_notifications_organization_members.delay(
            with_permissions=dict(can_edit_organization=True),
            members_organization_id=membership.organization_id,
            sender_id=membership.user_id,
            mode=NOTIFICATION_MODE_PERSONAL,
            notification_type=NOTIFICATION_TYPE_DISMISS_JOB,
            title=DISMISS_JOB_TITLE,
            description=DISMISS_JOB_DESCRIPTION.format(position=membership.role.title),
            organization_id=membership.organization_id,
            extra_data=dict(position=membership.role.title)
        ))
        return membership.delete()

    @classmethod
    def add_employee(cls, organization: Organization, employee: User, role: Role, added_by: User) -> Membership:
        from organizations.services.organization_services import OrganizationService

        if employee == organization.owner:
            raise NotAcceptableException(_('Insufficient rights'))

        if not role.organization == organization:
            raise NotAcceptableException(_('No such role in organization'))

        if not OrganizationService.user_can_edit_organization(organization=organization, user=added_by):
            raise NotAcceptableException(_('No rights to edit organization'))

        return cls.create(organization=organization, user=employee, role=role, added_by=added_by)

    @classmethod
    def add_employee_to_resume_org(cls, organization: Organization, employee: User, role: Role, added_by: User) -> Membership:
        from organizations.services.organization_services import OrganizationService

        if not role.organization == organization:
            raise NotAcceptableException(_('No such role in organization'))

        if not OrganizationService.user_can_edit_organization(organization=organization, user=added_by):
            raise NotAcceptableException(_('No rights to edit organization'))

        return cls.create(organization=organization, user=employee, role=role, added_by=added_by)

    @classmethod
    def update_role(cls, membership: Membership, new_role: Role) -> Membership:
        if not new_role.organization == membership.organization:
            raise NotAcceptableException(_('No such role in organization'))
        try:
            old_position = membership.role
            membership.role = new_role
            membership.save()
            transaction.on_commit(lambda: sent_notification.delay(
                recipient_id=membership.user_id,
                sender_id=membership.added_by_id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NOTIFICATION_TYPE_CHANGE_JOB_POSITION,
                title=CHANGE_JOB_POSITION_TITLE,
                description=CHANGE_JOB_POSITION_DESCRIPTION.format(old_position=old_position.title,
                                                                   new_position=new_role.title),
                organization_id=membership.organization_id,
                extra_data=dict(membership_id=membership.id,
                                can_edit_organization=membership.role.can_edit_organization,
                                old_position=old_position.title,
                                new_position=new_role.title)
            ))
            transaction.on_commit(lambda: send_notifications_organization_members.delay(
                with_permissions=dict(can_edit_organization=True),
                exclusion=[membership.user_id],
                members_organization_id=membership.organization_id,
                sender_id=membership.user_id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NOTIFICATION_TYPE_CHANGE_JOB_POSITION_OWNER,
                title=CHANGE_JOB_POSITION_OWNER_TITLE,
                description=CHANGE_JOB_POSITION_OWNER_DESCRIPTION.format(old_position=old_position.title,
                                                                         new_position=new_role.title),
                organization_id=membership.organization_id,
                extra_data=dict(membership_id=membership.id, can_edit_organization=True,
                                old_position=old_position.title,
                                new_position=new_role.title)
            ))
            return membership
        except IntegrityError:
            raise IntegrityException(_('Could not update role'))

    @classmethod
    def has_edit_rights_in_any_organization(cls, user: User) -> bool:
        return Membership.objects.filter(user=user, role__can_edit_organization=True).exists()

    @classmethod
    def has_seller_stats_rights_in_any_organization(cls, user: User, organization: Organization) -> bool:
        member = Membership.objects.filter(Q(user=user) & Q(organization=organization))
        return member.filter(role__can_see_stats=True).exists() or member.filter(
            role__can_edit_organization=True).exists() or member.filter(
            role__can_sale=True).exists() or user == organization.owner

    @classmethod
    def is_organization_member(cls, user: User, organization: Organization):
        return Membership.objects.filter(user=user, organization=organization).exists()

    @classmethod
    def is_organization_member_or_owner(cls, user: User, organization: Organization):
        return (Membership.objects.filter(user=user, organization=organization).exists() or user == organization.owner)


class RoleService:
    @classmethod
    def get(cls, *args, **kwargs) -> Membership:
        try:
            return Role.objects.get(*args, **kwargs)
        except Role.DoesNotExist:
            raise ObjectNotFoundException(_('Role not found'))

    @classmethod
    def filter(cls, *args, **kwargs):
        return Role.objects.filter(*args, **kwargs)
