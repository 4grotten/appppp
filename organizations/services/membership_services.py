from django.db import IntegrityError
from django.db.models import QuerySet

from common.exceptions import ObjectNotFoundException, NotAcceptableException, IntegrityException
from organizations.models import Membership, Organization, Role
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
            Membership.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException('Could not add employee')

    @classmethod
    def get_organization_employees(cls, organization: Organization) -> QuerySet:
        return Membership.objects.filter(organization=organization).order_by('role')

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
            membership.role = new_role
            membership.save()
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
