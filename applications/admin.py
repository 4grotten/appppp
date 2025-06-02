from django.contrib import admin

from applications.models import UserAppCategory, UserAppType, UserAppBanner, UserApp


@admin.register(UserAppCategory)
class UserAppCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(UserAppType)
class UserAppTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'is_adult')
    list_filter = ('category', 'is_adult')
    search_fields = ('title',)


@admin.register(UserAppBanner)
class UserAppBannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('image__file',)


@admin.register(UserApp)
class UserAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'app_link', 'price')
    list_filter = ('types',)
    search_fields = ('title', 'description', 'owner__email')
    filter_horizontal = ('types', 'banners', 'app_images')