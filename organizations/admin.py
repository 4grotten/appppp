from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets.widgets import GooglePointFieldWidget

from .models import (
    Organization, OrganizationType, OrganizationCategory, PhoneNumber,
    SocialNetworkContact, Role, Membership, DiscountCard, Subscription, OrganizationClientFinancialStatus
)


class OrganizationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display = ('title', 'owner', 'opens_at', 'closes_at', 'currency', 'address', 'is_active')
    list_filter = ('is_active',)


class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    list_filter = ('category',)


class OrganizationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('organization', 'phone_number',)


class SocialNetworkContactAdmin(admin.ModelAdmin):
    list_display = ('organization', 'url',)


class RoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'can_sale', 'can_check_attendance',
                    'can_see_stats', 'can_edit_organization',)


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role',)
    list_filter = ('organization', 'user', 'role',)


class DiscountCardAdmin(admin.ModelAdmin):
    list_display = ('organization', 'type', 'percent', 'limit', 'is_published', 'next_cumulative',)
    list_filter = ('type', 'is_published', 'organization',)


class OrganizationClientFinancialStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'organization', 'total_spent',)
    list_filter = ('card', 'user',)
    readonly_fields = ('total_spent',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'card':
            kwargs["queryset"] = DiscountCard.objects.filter(type=DiscountCard.CUMULATIVE)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user',)
    list_filter = ('organization', 'user',)


admin.site.register(OrganizationCategory, OrganizationCategoryAdmin)
admin.site.register(OrganizationType, OrganizationTypeAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(SocialNetworkContact, SocialNetworkContactAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(DiscountCard, DiscountCardAdmin)
admin.site.register(OrganizationClientFinancialStatus, OrganizationClientFinancialStatusAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
