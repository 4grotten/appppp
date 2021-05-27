from instagrapi import Client

from instagram_parsers.services.proxy_services import ProxyServices, LoginDeviceService


def get_instagram_user_info(username: str):
    settings = LoginDeviceService.get_random_login_settings()
    proxy = ProxyServices.get_random_formed_proxy()
    if proxy is not None:
        cl = Client(settings=settings, proxy=proxy)
    else:
        cl = Client(settings=settings)
    response_dict = dict(cl.user_info_by_username(username=username))
    user_info = {
        'user_id': response_dict['pk'],
        'full_name': response_dict['full_name'],
        'profile_image': str(response_dict['profile_pic_url']),
    }
    return user_info
