from rest_framework.permissions import BasePermission

from organizations.services.membership_services import MembershipService
from organizations.services.organization_services import OrganizationService


class IsAnyOrganizationOwnerOrAdmin(BasePermission):
    """
    Allows access to users who are owners or have "can_edit" permission in any organization
    """

    def has_permission(self, request, view):
        return OrganizationService.filter(
            owner=request.user).exists() or MembershipService.has_edit_rights_in_any_organization(user=request.user)
