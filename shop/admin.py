from django.contrib import admin

from shop.models import MainCategory, ItemCategory, ShopItem, YoutubeLink


class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru',)


class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_category', 'name_ru',)
    list_filter = ('main_category', 'organization',)


class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'category', 'price',)
    list_filter = ('category', 'organization',)


class YoutubeLinkAdmin(admin.ModelAdmin):
    list_display = ('link', 'item')


admin.site.register(MainCategory, MainCategoryAdmin)
admin.site.register(ItemCategory, ItemCategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(YoutubeLink, YoutubeLinkAdmin)
