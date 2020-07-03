from django.contrib import admin

from .models import (
    Organization, OrganizationType, OrganizationCategory, PhoneNumber,
    SocialNetworkContact, Role, Membership
)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'opens_at', 'closes_at',)


class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')


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


admin.site.register(OrganizationCategory, OrganizationCategoryAdmin)
admin.site.register(OrganizationType, OrganizationTypeAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(SocialNetworkContact, SocialNetworkContactAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Membership, MembershipAdmin)
