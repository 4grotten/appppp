from rest_framework import permissions

from organizations.services.organization_services import OrganizationService


class CanEditItemCategory(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.organization is None:
            return False
        return OrganizationService.user_can_edit_organization(user=request.user, organization=obj.organization)
