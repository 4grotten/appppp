from django.contrib import admin
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory


class ShopItemSizeInLine(admin.TabularInline):
    model = SizeFormat
    extra = 0


class FormatCriteriaLine(admin.TabularInline):
    model = FormatCriteria
    extra = 0


@admin.register(CriteriaSubcategory)
class CriteriaSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'name_en', 'name_tr',)
    search_fields = ('name',)
    filter_horizontal = ['format_criteria', ]


@admin.register(FormatCriteria)
class FormatCriteriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'name_en', 'name_tr',)
    search_fields = ('name',)
    inlines = (ShopItemSizeInLine,)


@admin.register(SizeFormat)
class SizeFormatAdmin(admin.ModelAdmin):
    list_display = ('size', 'format_criteria', 'order')
