import random
from typing import Optional

from django.utils.timezone import now
from instagrapi import Client

from instagram_parsers.models import Proxy, LoginDevice


class InstagramClientService:
    @classmethod
    def get_client(cls, for_getting_username: bool = False) -> Client:
        settings = LoginDeviceService.get_random_login_settings()
        proxy = ProxyService.get_random_formed_proxy(for_getting_username=for_getting_username)
        return Client(settings=settings, proxy=proxy)


class ProxyService:
    @classmethod
    def get_random_formed_proxy(cls, for_getting_username: bool = False) -> Optional[str]:
        proxies = Proxy.objects.filter(for_getting_username=for_getting_username, expires_at__gt=now())
        if proxies:
            random_proxy = random.choice(proxies)
            return f'https://{random_proxy.login}:{random_proxy.password}@{random_proxy.http_s}'
        return None


class LoginDeviceService:
    @classmethod
    def get_random_login_settings(cls) -> dict:
        login_settings = LoginDevice.objects.all()
        if not login_settings:
            raise Exception('Need at least one LoginDevice')
        random_device = random.choice(login_settings)
        return random_device.settings
