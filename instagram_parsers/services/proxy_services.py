import random

from instagram_parsers.models import Proxy, LoginDevice


class ProxyServices:
    @classmethod
    def get_random_formed_proxy(cls):
        proxies = Proxy.objects.all()
        if proxies:
            random_proxy = random.choice(proxies)
            str_proxy = 'https://' + str(random_proxy.login) + ':' + str(
                random_proxy.password) + '@' + str(random_proxy.http_s)
            return str_proxy
        return None


class LoginDeviceService:
    @classmethod
    def get_random_login_settings(cls) -> dict:
        login_settings = LoginDevice.objects.all()
        if not login_settings:
            raise Exception('Need at least one LoginDevice')
        random_device = random.choice(login_settings)
        return random_device.settings
