from django.contrib import admin

from instagram_parsers.models import Proxy, LoginDevice


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ('id', 'http_s', 'socks5', 'login', 'password')


@admin.register(LoginDevice)
class LoginDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
