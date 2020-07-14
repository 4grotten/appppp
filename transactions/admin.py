from django.contrib import admin

from .models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'client', 'organization', 'processed_by', 'is_processed', 'currency',
        'original_amount', 'discount_percent', 'discounted_amount', 'discount_type',
    )
    list_filter = (
        'is_processed', 'discount_percent', 'discount_type',
        'organization', 'client', 'processed_by', 'currency',
    )
    readonly_fields = ('is_processed', 'discounted_amount', 'source_card',)


admin.site.register(Transaction, TransactionAdmin)
