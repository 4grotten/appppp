import re

from instagrapi import Client

cl = Client()
cl.login('apofiztest1', 'passnotsecret')
settings_for_login = cl.get_settings()


def usernametoid(name: str):
    try:
        return cl.user_id_from_username(name)
    except IndexError:
        return "Wrong username!"
    except ConnectionError:
        return "Connection error!"


def get_username_from_instagram_url(url: str) -> str:
    return (re.findall('(?:https?:)?\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?P<username>[A-Za-z0-9_](?:(?:['
                       'A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_])))', url))[0]
