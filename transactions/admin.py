from django.contrib import admin

from .models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'organization', 'processed_by', 'is_processed', 'currency',
        'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback', 'final_amount',
        'type', 'discount_type', 'created_at', 'updated_at', 'display_time', 'status'
    )
    list_filter = (
        'is_processed', 'type', 'discount_type', 'discount_percent',
        'organization', 'client', 'processed_by', 'currency',
    )
    search_fields = ('id',)
    readonly_fields = (
        'is_processed', 'discount_percent', 'savings',
        'from_cashback', 'to_cashback', 'final_amount',
        'source_card', 'created_at', 'updated_at',
        'status'
    )

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Transaction, TransactionAdmin)
