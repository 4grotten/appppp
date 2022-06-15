from django.contrib import admin

# Register your models here.
from stock.models import FormatSize, ShopItemSize


@admin.register(FormatSize)
class FormatSizeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ShopItemSize)
class ShopItemSizeAdmin(admin.ModelAdmin):
    list_display = ('size', 'format_size', 'order')
