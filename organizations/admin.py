import json
from pathlib import Path

from django.contrib import admin
from django.contrib.gis.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from mapwidgets.widgets import GooglePointFieldWidget

from common.utils import DecimalDecoder, DecimalEncoder
from .models import (
    Organization, OrganizationType, OrganizationCategory, PhoneNumber,
    SocialNetworkContact, Role, Membership, DiscountCard, Subscription, OrganizationClientFinancialStatus,
    CardBackground, Partnership, Banner, Message, Attendance, CashbackGroup, CumulativeGroup, InstagramIntegration,
    CommonItemsGroup, Hotlink, OrganizationPromo, PromoSubscriber, PromoEditLog, HotlinkCollectionItem,
    HotlinkCollectionSubcategory, HotlinkCollectionLink, Service, OrganizationVerificationUsers, OrganizationBlacklist,
    BlockedUser, OrganizationPaymentSystemUsers, Question, Assistant, Answer, AnswerFile, Plan, UserAssistant, Chat,
    ChatMessage, RegionalTariff, PaymentSystemMethod, OrganizationBanner
)
from .serializers.assistant_serializers import AnswerFileSerializer


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
            'fields': ('freedompay_activated', 'paysy_activated', 'libersave_activated', 'betapay_activated',
                       'cryptocloud_activated', 'payment_systems_activated', 'payment_with_confirmation',
                       'freedompay_confirmed', 'paysy_confirmed', 'libersave_confirmed', 'betapay_confirmed',
                       'cryptocloud_confirmed')
        }),
        ('Status of Organization', {
            'fields': ('is_active', 'is_deleted', 'is_banned', 'is_private', 'is_under_review', 'is_delivery_service',
                       'is_bank', 'is_wholesale', 'can_update_is_wholesale', 'is_wholesale_request_timestamp',
                       'has_license', 'verification_status')
        }),
        ('Other configurations', {
            'fields': (
            'cashback_group', 'cumulative_group', 'items_group', 'running_purchase_id', 'switcher')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.avg_check == 0:
            obj.avg_check = None
        image_file = f'https://apofiz-media.s3.amazonaws.com/{obj.image.file.name}'
        small = f'https://apofiz-media.s3.amazonaws.com/{obj.image.small}'
        types = form.cleaned_data.get('types')
        types_list = [type.id for type in types]

        from organizations.serializers.organization_serializers import OrganizationMapsListSerializer
        is_show_on_map = OrganizationMapsListSerializer().get_is_show_on_map(obj)
        json_file_path = Path("organization_maps.json")
        if json_file_path.is_file():
            with open(json_file_path, 'r') as file:
                data = json.load(file, cls=DecimalDecoder)
                organization_data = next((org for org in data if org['id'] == obj.id), None)
                if organization_data:
                    organization_data['title'] = obj.title
                    organization_data['avg_check'] = obj.avg_check
                    organization_data['currency'] = obj.currency.code
                    organization_data['full_location']['latitude'] = None if not obj.location or not obj.location.y else obj.location.y
                    organization_data['full_location']['longitude'] = None if not obj.location or not obj.location.x else obj.location.x
                    organization_data['types'] = types_list
                    organization_data['image']['file'] = image_file
                    organization_data['image']['small'] = small
                    organization_data['country'] = obj.country.code
                    organization_data['city'] = obj.city.id
                    organization_data['verification_status'] = obj.verification_status
                    organization_data['has_delivery'] = obj.has_delivery
                    organization_data['has_self_pick_up'] = obj.has_self_pick_up
                    organization_data['has_license'] = obj.has_license
                    organization_data['freedompay_activated'] = obj.freedompay_activated
                    organization_data['paysy_activated'] = obj.paysy_activated
                    organization_data['libersave_activated'] = obj.libersave_activated
                    organization_data['betapay_activated'] = obj.betapay_activated
                    organization_data['cryptocloud_activated'] = obj.cryptocloud_activated
                    organization_data['payment_systems_activated'] = obj.payment_systems_activated
                    organization_data['payment_with_confirmation'] = obj.payment_with_confirmation
                    organization_data['freedompay_confirmed'] = obj.freedompay_confirmed
                    organization_data['paysy_confirmed'] = obj.paysy_confirmed
                    organization_data['libersave_confirmed'] = obj.libersave_confirmed
                    organization_data['betapay_confirmed'] = obj.betapay_confirmed
                    organization_data['cryptocloud_confirmed'] = obj.betapay_confirmed
                    organization_data['is_active'] = obj.is_active
                    organization_data['is_deleted'] = obj.is_deleted
                    organization_data['is_banned'] = obj.is_banned
                    organization_data['is_under_review'] = obj.is_under_review
                    organization_data['is_private'] = obj.is_private
                    organization_data['show_contacts'] = obj.show_contacts
                    organization_data['is_wholesale'] = obj.is_wholesale
                    organization_data['can_update_is_wholesale'] = obj.can_update_is_wholesale
                    organization_data['is_delivery_service'] = obj.is_delivery_service
                    organization_data['is_bank'] = obj.is_bank
                    organization_data['show_followers'] = obj.show_followers
                    organization_data['is_show_on_map'] = is_show_on_map
                    with open(json_file_path, 'w') as file:
                        json.dump(data, file, cls=DecimalEncoder)

        super().save_model(request, obj, form, change)
        if not change:
            from organizations.serializers.organization_serializers import OrganizationMapsListSerializer
            serialized_organization = OrganizationMapsListSerializer(obj).data
            json_file_path = Path("organization_maps.json")
            if json_file_path.is_file():
                with open(json_file_path, 'r') as file:
                    data = json.load(file, cls=DecimalDecoder)
                    data.append(serialized_organization)

                with open(json_file_path, 'w') as file:
                    json.dump(data, file, cls=DecimalEncoder)

    def delete_model(self, request, obj):
        json_file_path = Path("organization_maps.json")
        if json_file_path.is_file():
            with open(json_file_path, 'r') as file:
                data = json.load(file, cls=DecimalDecoder)
                data = [org for org in data if org['id'] != obj.id]

            with open(json_file_path, 'w') as file:
                json.dump(data, file, cls=DecimalEncoder)

        super().delete_model(request, obj)


    def delete_queryset(self, request, queryset):
        json_file_path = Path("organization_maps.json")
        if json_file_path.is_file():
            with open(json_file_path, 'r') as file:
                data = json.load(file, cls=DecimalDecoder)

            data = [org for org in data if org['id'] not in queryset.values_list('id', flat=True)]

            with open(json_file_path, 'w') as file:
                json.dump(data, file, cls=DecimalEncoder)

        super().delete_queryset(request, queryset)





@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_adult', 'title_ru', 'title_tr', 'title_de', 'title_zh')
    list_filter = ('category',)
    search_fields = ('title', 'title_ru', 'title_tr', 'category__name',)


@admin.register(OrganizationCategory)
class OrganizationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'name_tr', 'name_de', 'name_zh',)
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
    list_display = ('preview', 'ordering', 'name', 'name_ru', 'name_en', 'name_tr', 'name_de', 'name_zh')
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


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'ordering')
    list_editable = ('ordering', )
    search_fields = ('text', )

@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'name')
    search_fields = ('name', )

@admin.register(UserAssistant)
class UserAssistantAdmin(admin.ModelAdmin):
    list_display = ('id', 'assistant', 'user', 'active_until')
    search_fields = ('assistant', 'user', )

@admin.register(Plan)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name', )

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'assistant', 'question')
    search_fields = ('assistant', 'question', )

@admin.register(AnswerFile)
class AnswerFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'assistant', 'user')
    search_fields = ('assistant', 'user', )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'text')
    search_fields = ('chat', 'sender', 'text')


@admin.register(RegionalTariff)
class RegionalTariffAdmin(admin.ModelAdmin):
    list_display = ('country', 'tariff_type', 'original_price', 'discount', 'duration_months', 'total_price_display')
    list_filter = ('country', 'tariff_type')
    search_fields = ('country__name',)

    def total_price_display(self, obj):
        return format_html('<b>{}</b>', obj.total_price)
    total_price_display.short_description = 'Total Price'


@admin.register(PaymentSystemMethod)
class RegionalTariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'code')
    list_filter = ('name', 'is_active', 'code')
    search_fields = ('name', 'code')


@admin.register(OrganizationBanner)
class OrganizationBannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('id',)
    filter_horizontal = ('organizations',)
