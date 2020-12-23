import re

from instagrapi import Client

from common.exceptions import ObjectNotFoundException


def usernametoid(name: str):
    try:
        cl = Client()
        cl.login_by_sessionid('45149694492%3AjIq4vOZE7WPR9m%3A6')
        return cl.user_id_from_username(name)
    except IndexError:
        raise ObjectNotFoundException('Can not find instagram page')
    except ConnectionError:
        raise ObjectNotFoundException('Can not find instagram page')


def get_username_from_instagram_url(url: str) -> str:
    return (re.findall('(?:https?:)?\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?P<username>[A-Za-z0-9_](?:(?:['
                       'A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_])))', url))[0]
