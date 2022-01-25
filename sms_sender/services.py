import json

import requests
from django.conf import settings
from django.template import Template, Context
from django.utils.translation import gettext_lazy as _
from common.services import slack


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
        message = message + ' is your verification code'

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
        slack.bot(f'NIKITA\n{str(numbers[0])}\n {message}\n'
                  f' status_code-{response.status_code}\n==============================')
        if response.status_code == 200:
            return response.content.decode('utf-8')

        return Exception(_('Error while sending SMS'))


class MessageServiceSendPulse:

    @classmethod
    def send_sms(cls, numbers: str, message: str):
        if len(numbers) < 0:
            return
        sms_url = settings.SEND_PULSE_SMS_URL
        headers = cls.get_headers()
        payload = {
            "sender": f"{settings.SEND_PULSE_SENDER}",
            "phones": [f"{numbers}"],
            "body": f"{message}: is your verification code"
        }
        data = json.dumps(payload)
        response = requests.post(url=sms_url, data=data, headers=headers)
        # print(response.content)
        slack.bot(f'SAND_PULSE\n{str(numbers)}\n {message}\n '
                  f'status_code-{response.status_code}\n==============================')
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
        login_url = settings.SEND_PULSE_LOGIN_URL
        payload = {
            "grant_type": f"{settings.SEND_PULSE_GRAND_TYPE}",
            "client_id": f"{settings.SEND_PULSE_CLIENT_ID}",
            "client_secret": f"{settings.SEND_PULSE_CLIENT_SECRET}"
        }
        login_response = requests.post(login_url, data=payload)
        token = json.loads(login_response.text)["access_token"]
        return token


class MessageServiceSMSRU:
    @classmethod
    def send_sms(cls, numbers, message):
        login = settings.SMSCRU_LOGIN
        password = settings.SMSCRU_PASSWORD
        sms_url = f'https://smsc.ru/sys/send.php?login={login}&psw={password}&phones={numbers}' \
                  f'&mes={message}: is your verification code'
        response = requests.post(url=sms_url)
        # print(numbers)
        # print(response.content, response.status_code)
        slack.bot(f'SMSC_RU\n{str(numbers)}\n {message}: is your verification code\n status_code-{response.status_code}'
                  f'\n==============================')
        if response.status_code == 200:
            return response.content
        return Exception(_('Error while sending SMS'))


from twilio.rest import Client


class MessageServiceTwilio:
    @classmethod
    def send_sms(cls, number, code):
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN

        client = Client(account_sid, auth_token)
        sms = f'{code}: is your verification code'

        message = client.messages.create(
            to=number,
            from_=settings.TWILIO_PHONE,
            body=sms)
