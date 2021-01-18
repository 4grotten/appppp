from instagram_parsers.constants import LOGIN_SETTINGS
from instagram_parsers.parsers.get_id import usernametoid
from instagrapi import Client

from instagram_parsers.services.proxy_services import ProxyServices


def get_instagram_user_info(username: str):
    settings = LOGIN_SETTINGS
    proxy = ProxyServices.get_random_formed_proxy()
    if proxy is not None:
        cl = Client(settings=settings, proxy=proxy)
    else:
        cl = Client(settings=settings)
    user_id = usernametoid(username)
    user_info = dict(cl.user_info(user_id=user_id))
    full_name = user_info['full_name']
    profile_image = str(user_info['profile_pic_url'])
    return dict(full_name=full_name, profile_image=profile_image, user_id=user_id)
