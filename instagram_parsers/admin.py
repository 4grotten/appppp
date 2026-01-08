from django.contrib import admin
from django.utils import timezone

from instagram_parsers.models import Proxy, LoginDevice,InstagramApi
from instagram_parsers.parsers import parser


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
    list_display = ('id', 'for_getting_username', 'username', 'created_at', 'updated_at',)


    def save_model(self, request, obj, form, change):
        if not obj.settings:
            proxy = f'http://{obj.proxy_login}:{obj.proxy_password}@{obj.proxy_http_s}'
            obj.settings = parser.get_settings_login_device(obj.username, obj.password, proxy=proxy)
            obj.for_getting_username = True
        super().save_model(request, obj, form, change)


#
# @admin.register(InstagramApi)
# class InstagramApiAdmin(admin.ModelAdmin):
#     list_display = ('id', 'username', 'password', 'api_key', 'proxy', 'is_active','created_at', 'updated_at',)

    # def save_model(self, request, obj, form, change):
    #     if not obj.api_key:
    #         proxy = f'http://{obj.proxy.login}:{obj.proxy.password}@{obj.proxy.http_s}'
    #         obj.api_key = parser.get_api_key(obj.username, obj.password, proxy=proxy)
    #         obj.is_active = True
    #     super().save_model(request, obj, form, change)