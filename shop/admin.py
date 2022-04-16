from django.contrib import admin

from shop.models import (
    ItemCategory, ItemSubcategory, ShopItem, ItemBookmark, ItemLike, Complaint, Cart, CartItem,
    ItemInstagramData,
)
from .forms import ItemSubcategoryAdminForm


class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'is_adult',)
    search_fields = ('name',)
    raw_id_fields = ('icon',)


class InstagramDataInline(admin.TabularInline):
    model = ItemInstagramData
    extra = 0


class ItemSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'category', 'name_ru', 'organization',)
    list_filter = ('category', 'organization',)
    search_fields = ('name',)
    raw_id_fields = ('category', 'organization',)
    form = ItemSubcategoryAdminForm


class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'subcategory', 'price', 'discount', 'is_published', 'is_hidden',)
    list_filter = ('is_published', 'is_hidden', 'subcategory', 'organization',)
    search_fields = ('name',)
    raw_id_fields = ('organization', 'subcategory', 'images', 'videos')
    inlines = (InstagramDataInline,)


class ItemInstagramDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'thumbnail_url', 'video_url', 'updated_at', 'created_at',)
    raw_id_fields = ('item',)


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

admin.site.register(Complaint, ComplaintAdmin)
