import json
import requests
import re


def usernametoid(name):
    proxies = {'http': 'socks5://Selbulaone0912:B8g4KqW@89.191.233.151:45786', }
    try:
        response = requests.get('https://www.instagram.com/web/search/topsearch/?query=' + name, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Geko/20100101 Firefox/64.0'},
                                proxies=proxies).json()
        if response:
            return response['graphql']['user']['id']
    except IndexError:
        return "Wrong username!"
    except ConnectionError:
        return "Connection error!"


def get_username_from_instagram_url(url: str) -> str:
    return (re.findall('(?:https?:)?\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?P<username>[A-Za-z0-9_](?:(?:['
                       'A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_])))', url))[0]
