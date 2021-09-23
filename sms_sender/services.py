import json

import requests
from django.conf import settings
from django.core.cache import cache
from django.template import Template, Context
from django.utils.translation import gettext_lazy as _


class MessageServiceNIKITA:
    @classmethod
    def send_sms(cls, numbers: list, message: str, sms_id: str):
        if len(numbers) < 0:
            return

        template = '''<?xml version="1.0" encoding="UTF-8"?>
        <message>
            <login>{{ login }}</login>
            <pwd>{{ password }}</pwd>
            <id>{{ id }}</id>
            <sender>{{ sender }}</sender>
            <text>{{ text }}</text>
            <phones>
            {% for phone in phones %}    <phone>{{ phone }}</phone>{% endfor %}
            </phones>
            <test>{{ test }}</test>
        </message>
        '''

        context = {
            'login': settings.NIKITA_USERNAME,
            'password': settings.NIKITA_PASSWORD,
            'id': sms_id,
            'sender': settings.NIKITA_SENDER,
            'text': message,
            'phones': numbers,
            'test': settings.NIKITA_TEST_MODE
        }

        template = Template(template)
        data = template.render(Context(context))

        response = requests.post(
            settings.NIKITA_URL,
            data=data.encode('utf-8'),
            headers={'Content-Type': 'application/xml'}
        )

        if response.status_code == 200:
            return response.content.decode('utf-8')

        return Exception(_('Error while sending SMS'))


class MessageServiceSendPulse:

    # @classmethod
    # # def send_sms(cls, numbers: list, message: str, sms_id: str):
    # #     if len(numbers) < 0:
    # #         return
    # #     headers = cls.get_headers()
    # #     # login_response = requests.post(login_url, data=payload, headers=headers)
    # #     # response = requests.post(
    # #     #     settings.NIKITA_URL,
    # #     #     data=data.encode('utf-8'),
    # #     #     headers={'Content-Type': 'application/xml'}
    # #     # )
    # #     if response.status_code == 200:
    # #         return response.content.decode('utf-8')
    #
    #     return Exception(_('Error while sending SMS'))

    @classmethod
    def get_headers(cls):
        headers = {
            'Accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'X-Requested-With': 'XMLHttpRequest',
        }
        return headers

    @classmethod
    def login_send_pulse(cls):
        login_url = "https://api.sendpulse.com/oauth/access_token"
        payload = {
           "grant_type":"client_credentials",
           "client_id":"3968e5a4e06281d5da804dc05f17c192",
           "client_secret":"411baf48c1c91ef35f4c152b13f99962"
        }

        login_response = requests.post(login_url, data=payload)
        token = json.loads(login_response.text)["access_token"]
        print(token)
        return token

    @classmethod
    def get_token(cls):
        token = cache.get("token_send_pulse", None)
        print('token =====', token)
        if not token:
            print('token NOT IN CACHE ------------')
            token = cls.login_send_pulse()
            cache.set('token_send_pulse', token, timeout=settings.SMS_SENDPULSE_SESSION_ID_EXPIRED_TIME)
            print('NEW_token', token)
        return token