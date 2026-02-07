from django.contrib import admin
from django.utils.html import format_html

from .models import SavedContact


@admin.register(SavedContact)
class SavedContactAdmin(admin.ModelAdmin):
    """Admin configuration for SavedContact model."""

    list_display = [
        'full_name',
        'user',
        'phone',
        'email',
        'company',
        'avatar_preview',
        'created_at',
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['full_name', 'phone', 'email', 'company', 'position', 'user__phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'avatar_preview_large']
    autocomplete_fields = ['user', 'avatar']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'full_name', 'phone', 'email')
        }),
        ('Professional', {
            'fields': ('company', 'position')
        }),
        ('Avatar', {
            'fields': ('avatar', 'avatar_preview_large')
        }),
        ('Additional', {
            'fields': ('notes', 'payment_methods', 'social_links')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def avatar_preview(self, obj):
        """Display small avatar preview in list."""
        if obj.avatar and obj.avatar.file:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.file.url
            )
        return '-'
    avatar_preview.short_description = 'Avatar'

    def avatar_preview_large(self, obj):
        """Display large avatar preview in detail."""
        if obj.avatar and obj.avatar.file:
            return format_html(
                '<img src="{}" width="150" height="150" style="border-radius: 8px; object-fit: cover;" />',
                obj.avatar.file.url
            )
        return 'No avatar'
    avatar_preview_large.short_description = 'Avatar Preview'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'avatar')
