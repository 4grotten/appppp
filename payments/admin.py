from django.contrib import admin
from django.db.models import QuerySet

from organizations.admin import (
    AllowedOrganizationInline,
    PaymentSystemMethodAdmin,
)
from organizations.models import RegionalPaymentSystemSettings as OriginalSettings
from payments.models import (
    BetapaySettings,
    CryptoCloudSettings,
    FreedomPaySettings,
    LibersaveSettings,
    MaalyPayOrganizationPaymentSystem,
    MaalyPaySettings,
    PaymentSystemMethod,
    PaySySettings,
    ProfitgateOrganizationPaymentSystem,
    ProfitgateSettings,
    ZinaPayOrganizationPaymentSystem,
)


class BasePaymentSystemAdmin(admin.ModelAdmin):
    """Базовый класс админки для платёжных систем"""

    PAYMENT_SYSTEM_ID = None  # Переопределяется в наследниках

    list_display = (
        'get_countries_list',
        'is_enabled_in_region',
        'is_available_for_request',
        'is_available_for_ai',
        'get_override_count',
    )

    list_editable = (
        'is_enabled_in_region',
        'is_available_for_request',
        'is_available_for_ai',
    )

    search_fields = (
        'countries__name',
        'countries__code',
    )

    filter_horizontal = ('countries',)

    inlines = [AllowedOrganizationInline]

    fieldsets = (
        ('Страны (Countries)', {
            'fields': ('countries',),
            'description': 'Выберите страны, для которых применяются эти настройки'
        }),
        ('Настройки доступности', {
            'fields': ('is_enabled_in_region', 'is_available_for_request', 'is_available_for_ai'),
            'description': 'Управление доступностью платёжной системы в выбранных регионах'
        }),
    )

    def get_queryset(self, request) -> QuerySet:
        """Фильтруем только записи для данной платёжной системы"""
        qs = super().get_queryset(request)
        if self.PAYMENT_SYSTEM_ID:
            return qs.filter(payment_system_id=self.PAYMENT_SYSTEM_ID)
        return qs

    def get_countries_list(self, obj):
        """Отображение списка стран"""
        countries = obj.countries.all()
        count = countries.count()
        if count == 0:
            return "— (все страны)"
        elif count <= 5:
            return ", ".join([c.name for c in countries])
        else:
            first_five = ", ".join([c.name for c in countries[:5]])
            return f"{first_five}... (+{count-5})"
    get_countries_list.short_description = 'Страны'

    def get_override_count(self, obj):
        """Количество организаций-исключений"""
        count = obj.allowed_organizations.count()
        return f"{count} орг." if count > 0 else "—"
    get_override_count.short_description = 'Overrides'

    def save_model(self, request, obj, form, change):
        """Автоматически устанавливаем payment_system_id"""
        if self.PAYMENT_SYSTEM_ID:
            obj.payment_system_id = self.PAYMENT_SYSTEM_ID
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        """Разрешаем добавление только если нет записи для этой платёжки"""
        if self.PAYMENT_SYSTEM_ID:
            exists = OriginalSettings.objects.filter(
                payment_system_id=self.PAYMENT_SYSTEM_ID
            ).exists()
            return not exists
        return True


@admin.register(FreedomPaySettings)
class FreedomPayAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 1


@admin.register(PaySySettings)
class PaySySettingsAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 2


@admin.register(LibersaveSettings)
class LibersaveSettingsAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 3


@admin.register(BetapaySettings)
class BetapaySettingsAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 4


@admin.register(CryptoCloudSettings)
class CryptoCloudSettingsAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 5


class MaalyPayOrgInline(admin.TabularInline):
    """Инлайн для настроек MaalyPay организаций"""
    model = MaalyPayOrganizationPaymentSystem
    extra = 0
    verbose_name = "Настройки MaalyPay для организации"
    verbose_name_plural = "Настройки MaalyPay для организаций"
    fields = ('organization', 'merchant_id', 'api_key', 'bank_info')
    raw_id_fields = ('organization',)
    readonly_fields = ('api_key',)  # API key только для чтения в инлайне


@admin.register(MaalyPaySettings)
class MaalyPaySettingsAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 6


# Регистрируем отдельно настройки MaalyPay для организаций
@admin.register(MaalyPayOrganizationPaymentSystem)
class MaalyPayOrganizationAdmin(admin.ModelAdmin):
    """Админка для настроек MaalyPay организаций"""
    list_display = ['organization', 'merchant_id', 'get_currencies']
    search_fields = ['organization__name', 'merchant_id']
    autocomplete_fields = ['organization']
    list_select_related = ['organization']
    filter_horizontal = ('currencies',)

    fieldsets = (
        ('Организация', {
            'fields': ('organization',),
        }),
        ('Настройки MaalyPay', {
            'fields': ('merchant_id', 'api_key', 'bank_info'),
        }),
        ('Валюты', {
            'fields': ('currencies',),
            'description': 'Поддерживаемые валюты. Пусто = все валюты поддерживаются.'
        }),
    )

    def get_currencies(self, obj):
        currencies = obj.currencies.all()
        if currencies.exists():
            return ', '.join([c.code for c in currencies[:5]])
        return 'Все валюты'
    get_currencies.short_description = 'Валюты'


admin.site.register(PaymentSystemMethod, PaymentSystemMethodAdmin)



class ZinaPayOrgInline(admin.TabularInline):
    """Инлайн для настроек ZinaPay организаций"""
    model = ZinaPayOrganizationPaymentSystem
    extra = 0
    verbose_name = "Настройки ZinaPay для организации"
    verbose_name_plural = "Настройки ZinaPay для организаций"
    fields = ('organization', 'api_token', 'webhook_secret')
    raw_id_fields = ('organization',)
    readonly_fields = ('api_token',)


@admin.register(ZinaPayOrganizationPaymentSystem)
class ZinaPayOrganizationAdmin(admin.ModelAdmin):
    """Админка для настроек ZinaPay организаций"""
    list_display = ['organization', 'api_token', 'get_currencies']
    search_fields = ['organization__name', 'api_token']
    autocomplete_fields = ['organization']
    list_select_related = ['organization']
    filter_horizontal = ('currencies',)

    fieldsets = (
        ('Организация', {
            'fields': ('organization',),
        }),
        ('Настройки ZinaPay', {
            'fields': ('api_token', 'webhook_secret'),
        }),
        ('Валюты', {
            'fields': ('currencies',),
            'description': 'Поддерживаемые валюты. Пусто = все валюты поддерживаются.'
        }),
    )

    def get_currencies(self, obj):
        currencies = obj.currencies.all()
        if currencies.exists():
            return ', '.join([c.code for c in currencies[:5]])
        return 'Все валюты'
    get_currencies.short_description = 'Валюты'



class ProfitgateOrgInline(admin.TabularInline):
    """Инлайн для настроек Profitgate организаций"""
    model = ProfitgateOrganizationPaymentSystem
    extra = 0
    verbose_name = "Настройки Profitgate для организации"
    verbose_name_plural = "Настройки Profitgate для организаций"
    fields = ('organization', 'merchant_id', 'endpoint_id', 'api_secret')
    raw_id_fields = ('organization',)
    readonly_fields = ('api_secret',)


@admin.register(ProfitgateSettings)
class ProfitgateSettingsAdmin(BasePaymentSystemAdmin):
    PAYMENT_SYSTEM_ID = 8


@admin.register(ProfitgateOrganizationPaymentSystem)
class ProfitgateOrganizationAdmin(admin.ModelAdmin):
    """Админка для настроек Profitgate организаций"""
    list_display = ['organization', 'merchant_id', 'get_currencies']
    search_fields = ['organization__title', 'merchant_id']  # Используем title, так как мы фиксили эту ошибку
    autocomplete_fields = ['organization']
    list_select_related = ['organization']
    filter_horizontal = ('currencies',)

    fieldsets = (
        ('Организация', {
            'fields': ('organization',),
        }),
        ('Настройки Profitgate', {
            'fields': ('merchant_id', 'endpoint_id', 'api_secret'),
        }),
        ('Валюты', {
            'fields': ('currencies',),
            'description': 'Поддерживаемые валюты. Пусто = все валюты поддерживаются.'
        }),
    )

    def get_currencies(self, obj):
        currencies = obj.currencies.all()
        if currencies.exists():
            return ', '.join([c.code for c in currencies[:5]])
        return 'Все валюты'
    get_currencies.short_description = 'Валюты'
