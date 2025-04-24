import logging
import random
import time
from typing import Tuple

from django.utils.translation import gettext_lazy as _
from instagrapi import Client

from instagram_parsers.services.proxy_services import InstagramClientService


logger = logging.getLogger(__name__)
def get_data_from_post(dict_list):
    data_s = list()
    if dict_list['resources']:
        for resource in dict_list['resources']:
            if resource.get('video_url'):
                video_url = str(resource.get('video_url'))
            else:
                video_url = None
            data = dict(thumbnail_url=str(resource.get('thumbnail_url')), video_url=video_url,
                        pk=str((resource.get('pk'))))
            data_s.append(data.copy())
    else:
        if dict_list.get('video_url'):
            video_url = str(dict_list.get('video_url'))
        else:
            video_url = None
        data = dict(thumbnail_url=str(dict_list.get('thumbnail_url')),
                    video_url=video_url,
                    pk=str((dict_list.get('pk'))))
        data_s.append(data.copy())
    return data_s


def get_posts(user_id: int, posts_count: int, anonymous: bool = False):
    try:
        # if anonymous:
        #     cl = InstagramClientService.get_anon_client()
        # else:
        cl, login_device = InstagramClientService.get_client()
        try:
            media_list = cl.user_medias(user_id=user_id, amount=posts_count)
        except KeyError as e:
            # This helps you debug the actual content of the broken response
            logger.exception("Instagram user_medias failed — likely due to unexpected response structure")
            raise e
        post = list()
        for media in media_list:
            dict_list = media.dict()
            data_s = get_data_from_post(dict_list)
            code = dict_list.get('code')
            pk = str((dict_list.get('pk')))
            post_url = 'https://www.instagram.com/p/' + code + '/'
            post.append(
                dict(description=dict_list.get('caption_text'), created_at=dict_list.get('taken_at'),
                     post_url=post_url, pk=pk, data=data_s))
        return post
    except ConnectionError as e:
        return _("Connection Error")


def get_video_urls_from_post(post_url: str) -> Tuple[str, str]:
    cl, login_device = InstagramClientService.get_client()
    post_pk_from_url = cl.media_pk_from_url(url=post_url)
    media_info = cl.media_info(media_pk=post_pk_from_url)
    return media_info.video_url, media_info.thumbnail_url


def get_urls_from_post(post_url: str):
    cl, login_device = InstagramClientService.get_client()
    post_pk_from_url = cl.media_pk_from_url(url=post_url)
    media_info = cl.media_info(media_pk=post_pk_from_url)
    dict_list = media_info.dict()
    post_data = get_data_from_post(dict_list)
    return post_data


def get_settings_login_device(username, password, proxy, wait=60, max_retry=0):
    time.sleep(wait)
    result = {}
    if max_retry > 10:
        return {"uuids": {"uuid": "206ea907-d6ad-4d79-b2c0-d67e77e26b08", "phone_id": "d0eb57ab-9487-48f5-a709-fdce1b96e812", "device_id": "android-fde756e2092dfd25", "advertising_id": "9b658224-26c9-445a-a351-040ebf332ad1", "client_session_id": "28649e1b-d9c7-4aa4-9113-22833f51a8e2"}, "cookies": {"mid": "YTW1CAABAAGONdMoG-5XR2Ifg6SF", "rur": "\"CLN\\05446463092011\\0541662445711:01f7cde26c7253514a3ec72de4f6b5f9191a991655b567aa1ba31f43bd3da0a1287add60\"", "shbid": "\"1356\\05446463092011\\0541662445710:01f79d9db7c48ae29a2a7598096fc48a1c2d35857f0366cbf02057abd4bce55cca712b5f\"", "shbts": "\"1630909710\\05446463092011\\0541662445710:01f7da5378e42c05624700d1465c01010372a699762a7360518e0e1c3d705dec8cc59777\"", "csrftoken": "Zf9chsmKkwSnHvXlDBdTnQyyRVQNKnCH", "sessionid": "46463092011%3AC9gwjq8w8HKE9R%3A16", "ds_user_id": "46463092011"}, "last_login": 1630909711.7064524, "user_agent": "Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)", "device_settings": {"cpu": "samsungexynos9810", "dpi": "640dpi", "model": "star2qltecs", "device": "SM-G965F", "resolution": "1440x2560", "app_version": "105.0.0.18.119", "manufacturer": "samsung", "version_code": "168361634", "android_release": "9.0", "android_version": 28}}
    try:
        cl = Client()
        cl.set_proxy(proxy)
        time.sleep(random.uniform(1.5, 3.0))
        cl.login(username=username, password=password)

        result = cl.get_settings()
        return result
    except Exception:
        pass
    if not result:
        max_retry += 1
        wait = wait + 60
        result = get_settings_login_device(username, password, wait=wait, max_retry=max_retry, proxy=proxy)
    return result
