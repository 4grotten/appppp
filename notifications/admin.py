from django.contrib import admin

from .models import (
    Notification, NotificationSetting, NotificationMode
)


@admin.register(NotificationMode)
class NotificationAdmin(admin.ModelAdmin):
    pass


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'recipient', 'sender', 'is_read', 'model', 'type',)
    list_filter = ('is_read', 'mode', 'type', 'organization',)


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    pass
