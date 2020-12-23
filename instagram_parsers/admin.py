from django.contrib import admin

from instagram_parsers.models import Proxy


class ProxyAdmin(admin.ModelAdmin):
    list_display = ('id', 'http_s', 'socks5', 'login', 'password')


admin.site.register(Proxy, ProxyAdmin)
