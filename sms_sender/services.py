import json

import requests
from django.conf import settings
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

    @classmethod
    def send_sms(cls, numbers: str, message: str):
        if len(numbers) < 0:
            return
        sms_url = 'https://api.sendpulse.com/sms/send'
        headers = cls.get_headers()
        payload = {
            "sender":"Apofiz.com",
            "phones":[f"{numbers}"],
            "body": f"{message}",
            "transliterate":1,
            "route":{"UA":"sim_ua"},
            "emulate":0
        }
        data = json.dumps(payload)
        response = requests.post(url=sms_url, data=data, headers=headers)
        print(response.content)
        if response.status_code == 200:
            return response.content
        return Exception(_('Error while sending SMS'))

    @classmethod
    def get_headers(cls):
        token = cls.login_send_pulse()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
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
        return token
