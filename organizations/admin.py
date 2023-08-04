from django.contrib import admin
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe
from mapwidgets.widgets import GooglePointFieldWidget

from .models import (
    Organization, OrganizationType, OrganizationCategory, PhoneNumber,
    SocialNetworkContact, Role, Membership, DiscountCard, Subscription, OrganizationClientFinancialStatus,
    CardBackground, Partnership, Banner, Message, Attendance, CashbackGroup, CumulativeGroup, InstagramIntegration,
    CommonItemsGroup, Hotlink, OrganizationPromo, PromoSubscriber, PromoEditLog, HotlinkCollectionItem,
    HotlinkCollectionSubcategory, HotlinkCollectionLink, Service, OrganizationVerificationUsers, OrganizationBlacklist,
    BlockedUser, OrganizationPaymentSystemUsers
)


@admin.register(CashbackGroup)
class CashbackGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizations_in_group', 'created_at',)

    def organizations_in_group(self, group: CashbackGroup) -> int:
        return group.organizations.count()

@admin.register(OrganizationBlacklist)
class OrganizationBlacklistAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization',)

@admin.register(BlockedUser)
class OrganizationBlacklistAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization',)

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
    fields = ('type', 'limit', 'organization', 'percent', 'currency', 'image', 'next_cumulative', 'is_published')
    readonly_fields = (
    'type', 'limit', 'organization', 'percent', 'currency', 'image', 'next_cumulative', 'is_published')
    extra = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class MembershipInLine(admin.TabularInline):
    model = Membership
    raw_id_fields = ('user', 'role', 'added_by',)


class OrganizationVerificationUsersInLine(admin.TabularInline):
    model = OrganizationVerificationUsers
    extra = 1


class OrganizationPaymentSystemUsersInLine(admin.TabularInline):
    model = OrganizationPaymentSystemUsers
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_select_related = True
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display_links = ('id', 'title')
    list_display = (
        'id', 'title', 'owner', 'currency', 'country', 'city', 'is_active', 'is_banned', 'is_private', 'cashback_group',
        'cumulative_group', 'items_group', 'is_delivery_service', 'add_item_date', 'avg_check')
    list_filter = ('is_active', 'types__category', 'country', 'cashback_group', 'cumulative_group', 'items_group',
                   'is_delivery_service')
    search_fields = ('title',)
    raw_id_fields = ('owner', 'country', 'city', 'image', 'cashback_group', 'cumulative_group', 'items_group',)

    inlines = (
        PhoneInline,
        SocialInline,
        DiscountInline,
        OrganizationVerificationUsersInLine,
        OrganizationPaymentSystemUsersInLine, # 2:18
        MembershipInLine,
    )
    fieldsets = (
        ('General Information', {
            'fields': ('owner', 'title', 'title_lang', 'description', 'description_lang', 'address', 'location',
                       'currency', 'country', 'city', 'image', 'types', 'avg_check', 'show_contacts')
        }),
        ('Timings', {
            'fields': ('opens_at', 'closes_at')
        }),
        ('Types of Delivery', {
            'fields': ('has_delivery', 'has_self_pick_up')
        }),
        ('Payment Systems', {
            'fields': ('freedompay_activated', 'embily_activated', 'cryptobox_activated', 'payment_systems_activated',
                       'freedompay_confirmed', 'embily_confirmed', 'cryptobox_confirmed')
        }),
        ('Status of Organization', {
            'fields': ('is_active', 'is_deleted', 'is_banned', 'is_private', 'is_under_review', 'is_delivery_service',
                       'is_bank', 'has_license', 'verification_status')
        }),
        ('Other configurations', {
            'fields': (
            'cashback_group', 'cumulative_group', 'items_group', 'running_purchase_id', 'switcher')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.avg_check == 0:
            obj.avg_check = None
        super().save_model(request, obj, form, change)


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_adult', 'title_ru', 'title_tr',)
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
    list_display = ('id', 'title', 'organization', 'can_sale', 'can_check_attendance',
                    'can_see_stats', 'can_edit_organization',)
    raw_id_fields = ('organization',)
    search_fields = ('title', 'organization__title')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role',)
    search_fields = ('organization__title', 'user__phone_number', 'role__title')
    raw_id_fields = ('organization', 'user', 'role')


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
    # readonly_fields = (
    #     'organization', 'type', 'limit', 'percent', 'currency', 'is_published', 'next_cumulative', 'image'
    # )


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
        'id', 'requested_by', 'accepted_by', 'is_accepted',
        'can_check_attendance', 'can_see_stats', 'can_edit_organization', 'can_share_cashback', 'can_share_cumulative',
        'can_share_items',
    )
    raw_id_fields = ('requested_by', 'accepted_by')
    search_fields = ('requested_by__title', 'accepted_by__title')


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
    list_filter = ('link_type', 'organization',)
    raw_id_fields = ('organization', 'image')


@admin.register(HotlinkCollectionItem)
class HotlinkCollectionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotlink', 'item')
    raw_id_fields = ('hotlink', 'item')


@admin.register(HotlinkCollectionSubcategory)
class HotlinkCollectionSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotlink', 'subcategory')
    raw_id_fields = ('hotlink', 'subcategory')


@admin.register(HotlinkCollectionLink)
class HotlinkCollectionLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotlink', 'content', 'linked_item')
    list_filter = ('hotlink',)
    raw_id_fields = ('hotlink', 'linked_item')


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


@admin.register(Service)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('preview', 'ordering', 'name', 'name_ru', 'name_en', 'name_tr',)
    list_filter = ('name',)
    search_fields = ('name', 'icon', 'subcategory',)
    raw_id_fields = ('icon',)
    filter_horizontal = ['subcategory', 'category_of_item']

    readonly_fields = ['preview']

    def save_model(self, request, obj, form, change):
        change_service = Service.objects.filter(ordering=obj.ordering).first()
        if change_service:
            if obj.id:
                service = Service.objects.get(id=obj.id)
                change_number = change_service.ordering
                obj.ordering = change_number
                change_service.ordering = service.ordering
                change_service.save()
        super().save_model(request, obj, form, change)

    def preview(self, obj):
        try:
            if obj.icon.file:
                return mark_safe(f'<img src="{obj.icon.small.url}">')
        except AttributeError:
            pass
