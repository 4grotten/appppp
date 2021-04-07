from django.contrib import admin

from shop.models import (
    ItemCategory, ItemSubcategory, ShopItem, ItemBookmark, ItemLike, Complaint, Cart, CartItem, DeliveryInfo,
    ItemInstagramData,
)
from .forms import ItemSubcategoryAdminForm


class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'is_adult',)


class InstagramDataInline(admin.TabularInline):
    model = ItemInstagramData
    extra = 0


class ItemSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'name_ru', 'organization',)
    list_filter = ('category', 'organization',)
    form = ItemSubcategoryAdminForm


class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'subcategory', 'price', 'is_published', 'is_hidden',)
    list_filter = ('subcategory', 'organization',)
    inlines = (InstagramDataInline,)


class ItemInstagramDataAdmin(admin.ModelAdmin):
    list_display = ('item', 'post_pk', 'thumbnail_url', 'video_url')


class ItemLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


class ItemBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'id', 'organization', 'is_open', 'transaction',)
    list_filter = ('is_open',)
    raw_id_fields = ('user',)


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'item', 'count',)


class DeliveryInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'phone',)


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


admin.site.register(ItemInstagramData, ItemInstagramDataAdmin)
admin.site.register(ItemCategory, MainCategoryAdmin)
admin.site.register(ItemSubcategory, ItemSubcategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(ItemLike, ItemLikeAdmin)
admin.site.register(ItemBookmark, ItemBookmarkAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(DeliveryInfo, DeliveryInfoAdmin)
admin.site.register(Complaint, ComplaintAdmin)
