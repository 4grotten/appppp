import re

from instagrapi import Client

from common.exceptions import ObjectNotFoundException


def usernametoid(name: str):
    try:
        settings = {'uuids': {'phone_id': 'cbe2558f-6488-462d-a9da-e069d84c7d97',
                              'uuid': '018dcf3b-a7fb-40ef-8f47-082c43eb1e77',
                              'client_session_id': '595c2fdc-4337-4617-acff-587b5e98ead9',
                              'advertising_id': '3a39e79a-c079-4106-9f94-3dfb4b216b9e',
                              'device_id': 'android-0fb569bd35d44c9f'},
                    'cookies': {'csrftoken': 'AbfdhBzdUvgrPspHp7OIQMBKW1nXWIuk', 'ds_user': 'apofiz.test',
                                'ds_user_id': '44841168607', 'mid': 'X-L23wABAAE6qERU8jcy95_wrjPB', 'rur': 'ASH',
                                'sessionid': '44841168607%3AxmZxf4IjgpXSS4%3A4',
                                'urlgen': '"{212.112.119.146: 12764}:1kryvI:aYjqVptuXjMk8OALZh2zWpzvG8c"'},
                    'last_login': 1608709870.392346,
                    'device_settings': {'app_version': '105.0.0.18.119', 'android_version': 28,
                                        'android_release': '9.0', 'dpi': '640dpi', 'resolution': '1440x2560',
                                        'manufacturer': 'samsung', 'device': 'SM-G965F', 'model': 'star2qltecs',
                                        'cpu': 'samsungexynos9810', 'version_code': '168361634'},
                    'user_agent': 'Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)'}
        cl = Client(settings=settings)
        return cl.user_id_from_username(name)
    except IndexError:
        raise ObjectNotFoundException('Can not find instagram page')
    except ConnectionError:
        raise ObjectNotFoundException('Can not find instagram page')


def get_username_from_instagram_url(url: str) -> str:
    return (re.findall('(?:https?:)?\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?P<username>[A-Za-z0-9_](?:(?:['
                       'A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_])))', url))[0]
