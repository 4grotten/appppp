from django.contrib import admin

from .models import (
    Notification, NotificationSetting
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    pass
