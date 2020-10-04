from django.contrib import admin

from shop.models import ItemCategory, ItemSubcategory, ShopItem, ItemBookmark, ItemLike, Complaint


class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru',)


class ItemSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'name_ru', 'organization',)
    list_filter = ('category', 'organization',)


class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'subcategory', 'price', 'is_published')
    list_filter = ('subcategory', 'organization',)


class ItemLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


class ItemBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


admin.site.register(ItemCategory, MainCategoryAdmin)
admin.site.register(ItemSubcategory, ItemSubcategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(ItemLike, ItemLikeAdmin)
admin.site.register(ItemBookmark, ItemBookmarkAdmin)
admin.site.register(Complaint, ComplaintAdmin)
