from django.contrib import admin

from applications.models import (
    UserAppBalance,
    UserAppCategory,
    UserAppTransaction,
    UserAppType,
    UserAppBanner,
    UserApp,
    AddedApp,
    UserAppPurchase,
    PlatformCommission,
    SystemAccounts,
)


@admin.register(UserAppCategory)
class UserAppCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(UserAppType)
class UserAppTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "is_adult")
    list_filter = ("category", "is_adult")
    search_fields = ("title",)


@admin.register(UserAppBanner)
class UserAppBannerAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "is_default")
    list_filter = ("is_default",)
    search_fields = ("image__file",)


@admin.register(UserApp)
class UserAppAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "app_link", "price")
    list_filter = ("types",)
    search_fields = ("title", "description", "owner__email")
    filter_horizontal = ("types", "banners", "app_images")


@admin.register(AddedApp)
class AddedAppAdmin(admin.ModelAdmin):
    list_display = ("user", "user_app", "created_at")
    list_filter = ("user",)
    search_fields = ("user__email", "user_app__title")
    autocomplete_fields = ("user", "user_app")
    ordering = ("-created_at",)


@admin.register(UserAppPurchase)
class UserAppPurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "app", "is_paid", "transaction")
    list_filter = ("is_paid", "app")
    search_fields = ("user__username", "user__email", "app__title", "transaction__id")
    autocomplete_fields = ("user", "app", "transaction")


@admin.register(PlatformCommission)
class PlatformCommissionAdmin(admin.ModelAdmin):
    list_display = ("commission_percent",)


@admin.register(UserAppTransaction)
class UserAppTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "user_app_purchase",
        "profit_amount",
        "currency",
        "original_amount",
        "created_at",
    )
    list_filter = ("currency", "created_at")
    search_fields = ("owner__username", "user_app_purchase__id")


@admin.register(UserAppBalance)
class UserAppBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "total_earned", "current_balance", "currency")
    search_fields = ("user__username",)


@admin.register(SystemAccounts)
class SystemAccountsAdmin(admin.ModelAdmin):
    list_display = ("username", "server")
    search_fields = "username"
