from django.contrib import admin

from .models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'organization', 'processed_by', 'is_processed', 'currency',
        'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback', 'final_amount',
        'discount_type', 'created_at', 'updated_at',
    )
    list_filter = (
        'is_processed', 'discount_percent', 'discount_type',
        'organization', 'client', 'processed_by', 'currency',
    )
    search_fields = ('id',)
    readonly_fields = (
        'is_processed', 'discount_percent', 'savings',
        'from_cashback', 'to_cashback', 'final_amount',
        'source_card', 'created_at', 'updated_at',
    )

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Transaction, TransactionAdmin)
