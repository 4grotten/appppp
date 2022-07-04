from django.contrib import admin
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, ShopItemSizeCount, StockCart, \
    ShopItemCollections


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


@admin.register(StockCart)
class StockCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop_item')


@admin.register(ShopItemSizeCount)
class ShopItemSizeCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'size_format', 'stock_cart', 'quantity', )


@admin.register(ShopItemCollections)
class ShopItemCollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'main_item')
    filter_horizontal = ['related_items', 'related_item_links']