from django.contrib import admin
from django.contrib.gis.db import models
from mapwidgets import GooglePointFieldWidget

from .models import File, Country, Currency, City


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    pass


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
