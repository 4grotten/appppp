import random
from typing import Optional

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from instagrapi import Client

from instagram_parsers.models import Proxy, LoginDevice


class InstagramClientService:
    @classmethod
    def get_client(cls, for_getting_username: bool = False) -> Client:
        login_device = LoginDeviceService.get_random_login_settings()
        # proxy = ProxyService.get_random_formed_proxy(for_getting_username=for_getting_username)
        proxy = f'http://{login_device.proxy.login}:{login_device.proxy.password}@{login_device.proxy.http_s}'
        return Client(settings=login_device.settings, proxy=proxy)

    @classmethod
    def get_anon_client(cls, for_getting_username: bool = False) -> Client:
        proxy = ProxyService.get_random_formed_proxy(for_getting_username=for_getting_username)
        return Client(proxy=proxy)

class ProxyService:
    @classmethod
    def get_random_formed_proxy(cls, for_getting_username: bool = False) -> Optional[str]:
        proxies = Proxy.objects.filter(for_getting_username=for_getting_username, expires_at__gt=now())
        if proxies:
            random_proxy = random.choice(proxies)
            return f'http://{random_proxy.login}:{random_proxy.password}@{random_proxy.http_s}'
        return None

    @classmethod
    def get_random_proxy_for_requests(cls, for_getting_username: bool = False):
        proxies = Proxy.objects.filter(for_getting_username=for_getting_username, expires_at__gt=now())
        if proxies:
            proxy = random.choice(proxies)
            list_proxies = [dict(https=f'http://{proxy.login}:{proxy.password}@{proxy.http_s}')]
            return list_proxies
        return None


class LoginDeviceService:
    @classmethod
    def get_random_login_settings(cls):
        login_settings = LoginDevice.objects.filter(for_getting_username=True)
        if not login_settings:
            raise Exception(_('Need at least one LoginDevice'))
        random_device = random.choice(login_settings)
        return random_device
