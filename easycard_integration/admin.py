"""Django admin for EasyCard Integration (read-only)."""

from django.contrib import admin

from .models import (
    EasyCardAdminSettings,
    EasyCardCard,
    EasyCardProfile,
    EasyCardTransaction,
    EasyCardUserRole,
)


class ReadOnlyAdmin(admin.ModelAdmin):
    """Base read-only admin for EasyCard models.

    All EasyCard models are managed by the EasyCard server,
    so we only allow viewing in Django admin.
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EasyCardProfile)
class EasyCardProfileAdmin(ReadOnlyAdmin):
    """Admin for EasyCard profiles (read-only)."""

    list_display = [
        "phone",
        "first_name",
        "last_name",
        "language",
        "created_at",
    ]
    list_filter = ["language", "gender", "created_at"]
    search_fields = ["phone", "first_name", "last_name"]
    readonly_fields = [
        "id",
        "user_id",
        "phone",
        "first_name",
        "last_name",
        "gender",
        "language",
        "avatar_url",
        "created_at",
        "updated_at",
    ]


@admin.register(EasyCardCard)
class EasyCardCardAdmin(ReadOnlyAdmin):
    """Admin for EasyCard cards (read-only)."""

    list_display = [
        "name",
        "type",
        "status",
        "balance",
        "last_four_digits",
        "expiry_date",
        "created_at",
    ]
    list_filter = ["type", "status", "created_at"]
    search_fields = ["name", "last_four_digits"]
    readonly_fields = [
        "id",
        "user_id",
        "type",
        "name",
        "status",
        "balance",
        "last_four_digits",
        "expiry_date",
        "annual_fee",
        "activated_at",
        "created_at",
        "updated_at",
    ]


@admin.register(EasyCardTransaction)
class EasyCardTransactionAdmin(ReadOnlyAdmin):
    """Admin for EasyCard transactions (read-only)."""

    list_display = [
        "type",
        "status",
        "amount",
        "currency",
        "fee",
        "merchant_name",
        "created_at",
    ]
    list_filter = ["type", "status", "currency", "created_at"]
    search_fields = ["merchant_name", "description", "reference_id"]
    readonly_fields = [
        "id",
        "user_id",
        "card_id",
        "type",
        "status",
        "amount",
        "currency",
        "fee",
        "exchange_rate",
        "original_amount",
        "original_currency",
        "merchant_name",
        "merchant_category",
        "recipient_card",
        "sender_name",
        "sender_card",
        "reference_id",
        "description",
        "metadata",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"


@admin.register(EasyCardUserRole)
class EasyCardUserRoleAdmin(ReadOnlyAdmin):
    """Admin for EasyCard user roles (read-only)."""

    list_display = ["user_id", "role", "created_at"]
    list_filter = ["role", "created_at"]
    readonly_fields = ["id", "user_id", "role", "created_at"]


@admin.register(EasyCardAdminSettings)
class EasyCardAdminSettingsAdmin(ReadOnlyAdmin):
    """Admin for EasyCard settings (read-only)."""

    list_display = ["category", "key", "value", "description", "updated_at"]
    list_filter = ["category", "updated_at"]
    search_fields = ["key", "description"]
    readonly_fields = [
        "id",
        "category",
        "key",
        "value",
        "description",
        "updated_by",
        "updated_at",
    ]
