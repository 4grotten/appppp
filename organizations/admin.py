from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets.widgets import GooglePointFieldWidget

from .models import (
    Organization, OrganizationType, OrganizationCategory, PhoneNumber,
    SocialNetworkContact, Role, Membership, DiscountCard, Subscription, OrganizationClientFinancialStatus,
    CardBackground, Partnership, Banner, Message, Attendance, CashbackGroup, CumulativeGroup, InstagramIntegration,
    CommonItemsGroup, Hotlink, OrganizationPromo, PromoSubscriber, PromoEditLog
)


@admin.register(CashbackGroup)
class CashbackGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizations_in_group', 'created_at',)

    def organizations_in_group(self, group: CashbackGroup) -> int:
        return group.organizations.count()


@admin.register(CumulativeGroup)
class CumulativeGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizations_in_group', 'created_at',)

    def organizations_in_group(self, group: CumulativeGroup) -> int:
        return group.organizations.count()


@admin.register(CommonItemsGroup)
class CommonItemsGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizations_in_group', 'created_at',)

    def organizations_in_group(self, group: CumulativeGroup) -> int:
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


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display = (
        'title', 'owner', 'currency', 'country', 'city', 'is_active', 'is_banned',
        'cashback_group', 'cumulative_group', 'items_group',
    )
    list_filter = ('is_active', 'types__category', 'country', 'cashback_group', 'cumulative_group', 'items_group')
    search_fields = ('title',)
    raw_id_fields = ('owner', 'country', 'city', 'image', 'cashback_group', 'cumulative_group', 'items_group',)

    inlines = (PhoneInline, SocialInline, DiscountInline,)


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'title_ru', 'title_tr',)
    list_filter = ('category',)
    search_fields = ('title', 'title_ru', 'title_tr', 'category__name',)


@admin.register(OrganizationCategory)
class OrganizationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'name_tr',)
    search_fields = ('name',)


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('organization', 'phone_number',)


@admin.register(SocialNetworkContact)
class SocialNetworkContactAdmin(admin.ModelAdmin):
    list_display = ('organization', 'url',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'can_sale', 'can_check_attendance',
                    'can_see_stats', 'can_edit_organization',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role',)
    list_filter = ('organization', 'user', 'role',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'organization', 'arrival_time', 'arrival_checked_by', 'arrival_checker_role', 'is_active',
        'departure_time', 'departure_checked_by', 'departure_checker_role',
    )
    list_filter = ('organization', 'is_active',)
    date_hierarchy = 'arrival_time'


@admin.register(DiscountCard)
class DiscountCardAdmin(admin.ModelAdmin):
    list_display = ('organization', 'type', 'limit', 'percent', 'currency', 'is_published', 'next_cumulative',)
    list_filter = ('type', 'is_published', 'organization',)
    readonly_fields = (
        'organization', 'type', 'limit', 'percent', 'currency', 'is_published', 'next_cumulative', 'image'
    )


@admin.register(OrganizationClientFinancialStatus)
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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user',)
    list_filter = ('organization', 'user',)


@admin.register(CardBackground)
class CardBackgroundAdmin(admin.ModelAdmin):
    pass


@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    list_display = (
        'requested_by', 'accepted_by', 'is_accepted',
        'can_check_attendance', 'can_see_stats', 'can_edit_organization', 'can_share_cashback', 'can_share_cumulative',
        'can_share_items',
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'host_organization', 'linked_organization', 'updated_at')
    list_filter = ('host_organization',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'organization', 'content')


@admin.register(Hotlink)
class HotlinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'content', 'link_type', 'linked_item', 'linked_organization',)
    raw_id_fields = ('organization', 'image')


@admin.register(InstagramIntegration)
class InstagramIntegrationLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'url')


@admin.register(OrganizationPromo)
class OrganizationPromoAdmin(admin.ModelAdmin):
    list_display = ('organization', 'total_cashback', 'cashback', 'granted_amount')


@admin.register(PromoEditLog)
class PromoEditLogAdmin(admin.ModelAdmin):
    list_display = ('promo', 'changed_by', 'created_at')


@admin.register(PromoSubscriber)
class PromoSubscriberAdmin(admin.ModelAdmin):
    list_display = ('organization', 'subscriber', 'cashback', 'created_at')
    raw_id_fields = ('organization', 'subscriber')
