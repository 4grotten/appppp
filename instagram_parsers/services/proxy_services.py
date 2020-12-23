import random

from instagram_parsers.models import Proxy


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
