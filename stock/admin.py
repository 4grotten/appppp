from django.contrib import admin
from stock.models import FormatSize, ShopItemSize


class ShopItemSizeInLine(admin.TabularInline):
    model = ShopItemSize
    extra = 0


@admin.register(FormatSize)
class FormatSizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'name_en', 'name_tr',)
    search_fields = ('name',)
    inlines = (ShopItemSizeInLine,)


@admin.register(ShopItemSize)
class ShopItemSizeAdmin(admin.ModelAdmin):
    list_display = ('size', 'format_size', 'order')
