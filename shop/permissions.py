from rest_framework import permissions

from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, ItemSubcategory


class CanEditItemSubcategory(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: ItemSubcategory):
        if obj.organization is None:
            return False
        return OrganizationService.user_can_edit_organization(user=request.user, organization=obj.organization)


class CanEditItem(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: ShopItem):
        return OrganizationService.user_can_edit_organization(user=request.user, organization=obj.organization)


class CanViewUnpublishedItem(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: ShopItem):
        if obj.is_published:
            return True
        elif not request.user.is_authenticated:
            return False
        return OrganizationService.user_can_edit_organization(user=request.user, organization=obj.organization) or \
               OrganizationService.user_can_edit_own_resume(user=request.user, organization=obj.organization)
