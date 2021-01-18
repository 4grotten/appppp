import re
from instagrapi import Client
from common.exceptions import ObjectNotFoundException
from instagram_parsers.constants import LOGIN_SETTINGS

from instagram_parsers.services.proxy_services import ProxyServices


def usernametoid(name: str):
    try:
        settings = LOGIN_SETTINGS
        proxy = ProxyServices.get_random_formed_proxy()
        if proxy is not None:
            cl = Client(settings=settings, proxy=proxy)
        else:
            cl = Client(settings=settings)
        return cl.user_id_from_username(name)
    except IndexError:
        raise ObjectNotFoundException('Can not find instagram page')
    except ConnectionError:
        raise ObjectNotFoundException('Can not find instagram page')


def get_username_from_instagram_url(url: str) -> str:
    return (re.findall('(?:https?:)?\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?P<username>[A-Za-z0-9_](?:(?:['
                       'A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_])))', url))[0]
