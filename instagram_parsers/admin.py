from django.contrib import admin
from django.utils import timezone

from instagram_parsers.models import Proxy, LoginDevice


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ('id', 'http_s', 'socks5', 'login', 'password', 'for_getting_username', 'expires_at', 'is_active')

    def is_active(self, obj):
        now = timezone.now()
        if obj.expires_at:
            if now > obj.expires_at:
                return False
            else:
                return True
    is_active.boolean = True


@admin.register(LoginDevice)
class LoginDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'for_getting_username', 'created_at', 'updated_at',)
