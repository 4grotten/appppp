from django.contrib import admin

from shop.models import ItemCategory, ItemSubcategory, ShopItem


class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru',)


class ItemSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'name_ru', 'organization',)
    list_filter = ('category', 'organization',)


class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'subcategory', 'price', 'is_published')
    list_filter = ('subcategory', 'organization',)


admin.site.register(ItemCategory, MainCategoryAdmin)
admin.site.register(ItemSubcategory, ItemSubcategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
