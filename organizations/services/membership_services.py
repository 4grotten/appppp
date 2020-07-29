from django.db.models import QuerySet

from common.exceptions import ObjectNotFoundException
from organizations.models import Membership, Organization, Role


class MembershipService:
    @classmethod
    def get(cls, *args, **kwargs) -> Membership:
        try:
            return Membership.objects.get(*args, **kwargs)
        except Membership.DoesNotExist:
            raise ObjectNotFoundException('Membership not found')

    @classmethod
    def get_organization_employees(cls, organization: Organization) -> QuerySet:
        return Membership.objects.filter(organization=organization).order_by('role')


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
