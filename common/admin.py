from django.contrib import admin
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe
from mapwidgets import GooglePointFieldWidget

from .models import File, Country, Currency, City, Version, OpenExchangeRates, Languages, UmaiWallet, MessageText


@admin.register(MessageText)
class MessageTextAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']


@admin.register(UmaiWallet)
class UmaiWalletAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'password', 'amount', 'activate', 'version', 'start_time', 'end_time']


@admin.register(Languages)
class LanguagesAdmin(admin.ModelAdmin):
    list_display = ('preview', 'code', 'national_language', 'language_en', 'language_ru', 'flag',)
    search_fields = ('code', 'language_ru',)
    raw_id_fields = ['flag']
    readonly_fields = ['preview']

    def preview(self, obj):
        try:
            if obj.flag:
                return mark_safe(f'<img src="{obj.flag.small.url}">')
        except AttributeError:
            pass


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'is_watermarked',)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'flag', 'currency', 'is_priority', 'is_active', 'name_ru', 'name_tr',)
    search_fields = ('code', 'name', 'currency__code', 'name_ru', 'name_tr',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }

    list_display = ('name', 'country', 'name_ru', 'name_tr', 'postal',)
    search_fields = ('name', 'country__code', 'country__name', 'name_ru', 'name_tr',)
    list_filter = ('country',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'name_ru', 'name_tr',)


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ('device', 'version', 'created_at', 'updated_at', 'force_update')


@admin.register(OpenExchangeRates)
class OpenExchangeRatesAdmin(admin.ModelAdmin):
    list_display = ['app_id', 'created_at', 'updated_at']
