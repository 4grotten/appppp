from django.contrib import admin

from .models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'organization', 'processed_by', 'is_processed', 'currency',
        'original_amount', 'discount_percent', 'savings', 'discount_type',
        'created_at', 'updated_at',
    )
    list_filter = (
        'is_processed', 'discount_percent', 'discount_type',
        'organization', 'client', 'processed_by', 'currency',
    )
    search_fields = ('id',)
    readonly_fields = (
        'is_processed', 'discount_percent', 'savings',
        'source_card', 'created_at', 'updated_at',
    )


admin.site.register(Transaction, TransactionAdmin)
