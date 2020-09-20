from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets.widgets import GooglePointFieldWidget

from .models import (
    Organization, OrganizationType, OrganizationCategory, PhoneNumber,
    SocialNetworkContact, Role, Membership, DiscountCard, Subscription, OrganizationClientFinancialStatus,
    CardBackground, Partnership, Banner, Message, Attendance, CashbackGroup
)


class CashbackGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizations_in_group', 'created_at',)

    def organizations_in_group(self, group: CashbackGroup) -> int:
        return group.organizations.count()


class PhoneInline(admin.TabularInline):
    model = PhoneNumber
    extra = 0


class SocialInline(admin.TabularInline):
    model = SocialNetworkContact
    extra = 0


class DiscountInline(admin.TabularInline):
    model = DiscountCard
    extra = 0


class OrganizationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display = ('title', 'owner', 'opens_at', 'closes_at', 'currency', 'address', 'is_active', 'cashback_group',)
    list_filter = ('is_active', 'types__category', 'cashback_group',)
    search_fields = ('title',)

    inlines = (PhoneInline, SocialInline, DiscountInline,)


class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    list_filter = ('category',)
    search_fields = ('title', 'category__name',)


class OrganizationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


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


class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'organization', 'arrival_time', 'arrival_checked_by', 'arrival_checker_role', 'is_active',
        'departure_time', 'departure_checked_by', 'departure_checker_role',
    )
    list_filter = ('organization', 'is_active',)
    date_hierarchy = 'arrival_time'


class DiscountCardAdmin(admin.ModelAdmin):
    list_display = ('organization', 'type', 'limit', 'percent', 'currency', 'is_published', 'next_cumulative',)
    list_filter = ('type', 'is_published', 'organization',)
    readonly_fields = (
        'organization', 'type', 'limit', 'percent', 'currency', 'is_published', 'next_cumulative', 'image'
    )


class OrganizationClientFinancialStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'organization', 'accrued_cashback', 'get_currency',)
    list_filter = ('card', 'user',)
    readonly_fields = ('user', 'card', 'organization', 'accrued_cashback', 'get_currency',)

    def get_currency(self, client_status: OrganizationClientFinancialStatus):
        return client_status.organization.currency

    get_currency.short_description = 'Currency'
    get_currency.admin_order_field = 'organization__currency'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'card':
            kwargs["queryset"] = DiscountCard.objects.filter(type=DiscountCard.CUMULATIVE)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user',)
    list_filter = ('organization', 'user',)


class CardBackgroundAdmin(admin.ModelAdmin):
    pass


class PartnershipAdmin(admin.ModelAdmin):
    list_display = (
        'requested_by', 'accepted_by', 'is_accepted',
        'can_check_attendance', 'can_see_stats', 'can_edit_organization', 'can_share_cashback', 'can_share_cumulative',
    )


class BannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'host_organization', 'linked_organization', 'updated_at')
    list_filter = ('host_organization',)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'organization', 'content')


admin.site.register(CashbackGroup, CashbackGroupAdmin)
admin.site.register(OrganizationCategory, OrganizationCategoryAdmin)
admin.site.register(OrganizationType, OrganizationTypeAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(SocialNetworkContact, SocialNetworkContactAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(DiscountCard, DiscountCardAdmin)
admin.site.register(OrganizationClientFinancialStatus, OrganizationClientFinancialStatusAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(CardBackground, CardBackgroundAdmin)
admin.site.register(Partnership, PartnershipAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(Message, MessageAdmin)
