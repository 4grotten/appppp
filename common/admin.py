from django.contrib import admin
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe
from mapwidgets import GooglePointFieldWidget

from common.forms import CountryAdminForm

from .models import (
    AIPromptSettings,
    BlockedIps,
    ChatGPTSettings,
    City,
    CommentsWallpaper,
    Country,
    CountryInvoiceInfo,
    Currency,
    File,
    FileVideo,
    Languages,
    LinkApp,
    MessageText,
    OpenExchangeRates,
    SmsServices,
    TemporaryCodeSwitcher,
    UmaiWallet,
    Version,
)


@admin.register(MessageText)
class MessageTextAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_display_links = ["id", "name"]


@admin.register(UmaiWallet)
class UmaiWalletAdmin(admin.ModelAdmin):
    list_display = [
        "wallet",
        "password",
        "amount",
        "activate",
        "version",
        "start_time",
        "end_time",
    ]


@admin.register(Languages)
class LanguagesAdmin(admin.ModelAdmin):
    list_display = (
        "preview",
        "code",
        "national_language",
        "language_en",
        "language_ru",
        "flag",
    )
    search_fields = (
        "code",
        "language_ru",
    )
    raw_id_fields = ["flag"]
    readonly_fields = ["preview"]

    def preview(self, obj):
        try:
            if obj.flag:
                return mark_safe(f'<img src="{obj.flag.small.url}">')
        except AttributeError:
            pass


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "file",
        "is_watermarked",
        "image_url",
        "created_at",
        "updated_at",
        "large",
        "medium",
        "small",
    )
    search_fields = ("id", "file")


@admin.register(LinkApp)
class LinkAppAdmin(admin.ModelAdmin):
    list_display = ("name_link",)


@admin.register(CommentsWallpaper)
class CommentsWallpaperAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_active",
        "web_image",
        "mobile_image",
        "web_wallpaper",
        "mobile_wallpaper",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "web_wallpaper",
        "mobile_wallpaper",
    )

    def web_wallpaper(self, obj):
        return mark_safe(f'<img src={obj.web_image.url} width="100" height="60">')

    def mobile_wallpaper(self, obj):
        return mark_safe(f'<img src={obj.mobile_image.url} width="60" height="100">')

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            CommentsWallpaper.objects.exclude(id=obj.id).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(FileVideo)
class FileVideo(admin.ModelAdmin):
    list_display = ("id", "thumbnail", "video", "video_url")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "flag",
        "currency",
        "is_priority",
        "is_active",
        "is_paid_subscription",
        "name_ru",
        "name_tr",
    )
    list_filter = ("is_paid_subscription", "is_active", "currency")
    search_fields = (
        "code",
        "name",
        "currency__code",
        "name_ru",
        "name_tr",
    )
    form = CountryAdminForm

    actions = ["mark_as_paid_subscription", "mark_as_free"]

    def mark_as_paid_subscription(self, request, queryset):
        queryset.update(is_paid_subscription=True)

    mark_as_paid_subscription.short_description = "Сделать страну платной"

    def mark_as_free(self, request, queryset):
        queryset.update(is_paid_subscription=False)

    mark_as_free.short_description = "Сделать страну бесплатной"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    formfield_overrides = {models.PointField: {"widget": GooglePointFieldWidget}}

    list_display = (
        "id",
        "name",
        "country",
        "name_ru",
        "name_tr",
        "postal",
    )
    search_fields = (
        "name",
        "country__code",
        "country__name",
        "name_ru",
        "name_tr",
    )
    list_filter = ("country",)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "name_ru",
        "name_tr",
    )


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("device", "version", "created_at", "updated_at", "force_update")


@admin.register(OpenExchangeRates)
class OpenExchangeRatesAdmin(admin.ModelAdmin):
    list_display = ["app_id", "created_at", "updated_at"]


@admin.register(SmsServices)
class SmsServicesAdmin(admin.ModelAdmin):
    pass


@admin.register(BlockedIps)
class BlockedIpsAdmin(admin.ModelAdmin):
    pass


@admin.register(TemporaryCodeSwitcher)
class TemporaryCodeSwitcherAdmin(admin.ModelAdmin):
    pass


@admin.register(CountryInvoiceInfo)
class CountryInvoiceInfoAdmin(admin.ModelAdmin):
    list_display = [
        "country",
        "name",
        "address",
        "email",
        "city",
        "tax",
        "tax_id",
    ]
    list_select_related = [
        "country",
    ]


@admin.register(AIPromptSettings)
class AIPromptSettingsAdmin(admin.ModelAdmin):
    """Admin for managing AI assistant prompts (used by TG bot and Web Chat)."""

    list_display = [
        "id",
        "is_active",
        "updated_at",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Status", {
            "fields": ("is_active",),
            "description": "Если выключено, используются дефолтные промпты из кода"
        }),
        ("Language Detection", {
            "fields": ("language_detection_rule",),
            "description": "Правило определения языка из контекста сообщений пользователя (TG бот определяет язык автоматически)"
        }),
        ("Language Instructions (Legacy)", {
            "fields": ("language_instruction_ru", "language_instruction_en"),
            "description": "Устаревшие инструкции для фиксированного языка (для обратной совместимости с Web Chat)",
            "classes": ("collapse",),
        }),
        ("Identity", {
            "fields": ("identity_template",),
            "description": "Шаблон идентичности ассистента. Переменные: {assistant_name}, {organization}, {position}, {gender}"
        }),
        ("Formatting", {
            "fields": ("formatting_rules",),
            "description": "Правила форматирования ответов"
        }),
        ("Scenario A: Discounts", {
            "fields": ("scenario_a_discounts",),
            "classes": ("collapse",),
        }),
        ("Scenario B: Products", {
            "fields": ("scenario_b_products",),
            "description": "⚠️ ВАЖНО: Используйте 'Товар/Product' и 'Ссылка/Link' для корректного парсинга в TG боте",
            "classes": ("collapse",),
        }),
        ("Scenario C: Contacts", {
            "fields": ("scenario_c_contacts",),
            "classes": ("collapse",),
        }),
        ("Scenario D: General Questions", {
            "fields": ("scenario_d_general",),
            "description": "ВАЖНО: Это сценарий для приветствий и общих вопросов"
        }),
        ("Ending Rule", {
            "fields": ("ending_rule",),
            "classes": ("collapse",),
        }),
        ("Few-shot Examples (RU)", {
            "fields": ("few_shot_example_greeting_ru", "few_shot_example_capabilities_ru"),
            "description": "Примеры ответов на русском"
        }),
        ("Few-shot Examples (EN)", {
            "fields": ("few_shot_example_greeting_en", "few_shot_example_capabilities_en"),
            "description": "Примеры ответов на английском"
        }),
        ("Contacts Example", {
            "fields": ("few_shot_example_contacts",),
        }),
        ("Search Rules", {
            "fields": ("search_rules",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        # Allow adding only if no records exist (singleton)
        return not AIPromptSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of singleton
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Signal will handle webhook sync
