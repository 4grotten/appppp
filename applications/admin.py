from django.contrib import admin

from applications.models import UserAppCategory, UserAppType, UserAppBanner, UserApp, AddedApp


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


@admin.register(AddedApp)
class AddedAppAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_app', 'created_at')
    list_filter = ('user',)
    search_fields = ('user__email', 'user_app__title')
    autocomplete_fields = ('user', 'user_app')
    ordering = ('-created_at',)