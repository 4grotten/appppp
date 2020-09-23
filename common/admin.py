from django.contrib import admin

from .models import File, Country, Currency, City


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    pass


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'flag', 'currency', 'is_priority', 'is_active',)
    search_fields = ('code', 'name', 'currency__code',)


@admin.register(City)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'country',)
    search_fields = ('name', 'country__code', 'country__name',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name',)
