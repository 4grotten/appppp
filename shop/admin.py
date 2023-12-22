from django.contrib import admin

from shop.models import (
    ItemCategory, ItemSubcategory, ShopItem, ItemBookmark, ItemLike, Complaint, Cart, CartItem,
    ItemInstagramData, Comment, CommentComplaint, Booking, ItemCollection, Ticket, ResumeInfo, ResumeInfoFile,
    ResumePhoneNumber, ResumeSocialNetwork, ResumeDetailInfo, ResumeWorkExperience
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
    filter_horizontal = ['criteria_subcategory', ]
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


class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'parent', 'text')


class ItemBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


class ItemCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'display_items')

    def display_items(self, obj):
        return ", ".join(str(item) for item in obj.items.all())
    display_items.short_description = 'Items'


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'id', 'organization', 'is_open', 'transaction',)
    list_filter = ('is_open',)
    raw_id_fields = ('user',)


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'item', 'count',)


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('user', 'item',)


class CommentComplaintAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment',)


class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'item', 'is_open', 'transaction', 'start_time', 'end_time')


class TicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'item', 'is_active', 'transaction')


class ResumeInfoAdmin(admin.ModelAdmin):
    list_display = ('item', 'gender', 'full_name', 'date_of_birth', 'languages')


class ResumeInfoFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'created_at')


class ResumePhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('item', 'phone_number')


class ResumeSocialNetworkAdmin(admin.ModelAdmin):
    list_display = ('item', 'url')


class ResumeDetailInfoAdmin(admin.ModelAdmin):
    list_display = ('item', 'text')


class ResumeWorkExperienceAdmin(admin.ModelAdmin):
    list_display = ('item', 'company_name', 'position', 'start_of_work', 'end_of_work', 'up_to_now')



admin.site.register(ItemInstagramData, ItemInstagramDataAdmin)
admin.site.register(ItemCategory, MainCategoryAdmin)
admin.site.register(ItemSubcategory, ItemSubcategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(ItemLike, ItemLikeAdmin)
admin.site.register(ItemBookmark, ItemBookmarkAdmin)
admin.site.register(ItemCollection, ItemCollectionAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CartItem, CartItemAdmin)

admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(CommentComplaint, CommentComplaintAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(ResumeInfo, ResumeInfoAdmin)
admin.site.register(ResumeInfoFile, ResumeInfoFileAdmin)
admin.site.register(ResumePhoneNumber, ResumePhoneNumberAdmin)
admin.site.register(ResumeSocialNetwork, ResumeSocialNetworkAdmin)
admin.site.register(ResumeDetailInfo, ResumeDetailInfoAdmin)
admin.site.register(ResumeWorkExperience, ResumeWorkExperienceAdmin)
