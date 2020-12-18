import hashlib
import string
import random
from instagrapi import Client

from instagram_parser import get_id
import json


# new class
class MyClient(Client):
    """_docstring_"""

    @staticmethod
    def _extract_rhx_gis(html):
        options = string.ascii_lowercase + string.digits
        text = ''.join([random.choice(options) for _ in range(8)])
        return hashlib.md5(text.encode()).hexdigest()


def get_posts(id):
    try:
        settings = {
            "uuids": {"phone_id": "35729fff-aa1e-4d6a-b889-1710df661a34",
                      "uuid": "887b0e44-3b83-4996-af14-b517c96fee2f",
                      "client_session_id": "1b9cd485-5107-4e20-9bae-28a695998d1c",
                      "advertising_id": "3723cd4c-d370-4073-8507-1eb7dbb32699",
                      "device_id": "android-71b445d43959effc"},
            "cookies": {"csrftoken": "cM4BSEdZA3FQ6bXIKcZEZ8CPiRJxRPWP", "ds_user": "ss115test",
                        "ds_user_id": "44745007017",
                        "mid": "X9napgABAAHAkPJXqGNLXYjl13_J", "rur": "PRN",
                        "sessionid": "44745007017%3AMBJ3TclCka5jaR%3A1",
                        "urlgen": "\"{158.181.250.169: 41750}:1kpTbP:boqWK79fxV5PWsmtzCmQdrw0xRA\""},
            "last_login": 1608112813.279875,
            "device_settings": {"app_version": "105.0.0.18.119", "android_version": 28, "android_release": "9.0",
                                "dpi": "640dpi", "resolution": "1440x2560", "manufacturer": "samsung",
                                "device": "SM-G965F",
                                "model": "star2qltecs", "cpu": "samsungexynos9810", "version_code": "168361634"},
            "user_agent": "Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)"}

        cl = Client(settings=settings)

        media_list = cl.user_medias(user_id=id, amount=50)
        posts = list()
        for media in media_list:
            images = list()
            videos = list()
            dict_list = media.dict()
            if dict_list['resources']:
                for resource in dict_list['resources']:
                    if resource['video_url']:
                        video_url = str(resource.get('video_url'))
                        thumbnail = str(resource.get('thumbnail_url'))
                        video = (dict(video_url=video_url, thumbnail=thumbnail).copy())
                        videos.append(video)
                    else:
                        image = dict(file=str(resource.get('thumbnail_url')),
                                     small=str(resource.get('thumbnail_url')),
                                     medium=str(resource.get('thumbnail_url')),
                                     large=str(resource.get('thumbnail_url')))
                        images.append(image.copy())
            else:
                if dict_list['video_url']:
                    video_url = str(dict_list.get('video_url'))
                    thumbnail = str(dict_list.get('thumbnail_url'))
                    video = (dict(video_url=video_url, thumbnail=thumbnail).copy())
                    videos.append(video)
                else:
                    image = dict(file=str(dict_list.get('thumbnail_url')),
                                 small=str(dict_list.get('thumbnail_url')),
                                 medium=str(dict_list.get('thumbnail_url')),
                                 large=str(dict_list.get('thumbnail_url')))
                    images.append(image.copy())
            posts.append(
                dict(images=images, videos=videos, description=dict_list.get('caption_text'),
                     created_at=dict_list.get('taken_at')))
        return posts

    except ConnectionError as e:
        return "Connection Error"
