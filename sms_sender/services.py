import json

import requests
from django.conf import settings
from django.template import Template, Context
from django.utils.translation import gettext_lazy as _
from twilio.base.exceptions import TwilioRestException

from common.models import SmsServices, BlockedIps
from common.services import slack
from sms_sender.models import SmsModel


class MessageServiceNIKITA:
    @classmethod
    def send_sms(cls, numbers: list, message: str, sms_id: str, code_id: int = None, ip_addr: str = None):
        if not BlockedIps.objects.filter(ip_address=ip_addr).exists():
            if SmsServices.objects.last().nikita_service:
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
                slack.bot(f'NIKITA\n{str(numbers[0])}\n {message}\n'
                          f'link code: https://apofiz.com/admin/users/temporarycode/{code_id}/change/\n'
                          f'ip: {ip_addr}\n'
                          f' status_code-{response.status_code}\n==============================')
                if response.status_code == 200:
                    return response.content.decode('utf-8')

                return Exception(_('Error while sending SMS'))
            else:
                slack.bot(f'NIKITA SERVICE IS OFF '
                          f'\n{str(numbers[0])}\n message - {message}\n'
                          f'\nip: {ip_addr}'
                          f'\n==============================')
        else:
            slack.bot(f'NIKITA SERVICE'
                      f'\n{str(numbers[0])}\n message - {message}\n'
                      f'ip: {ip_addr}\n'
                      f'THIS IP IN BLACK LIST!!! \n'
                      f'==============================')


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


class MessageServiceMessageBird:
    @classmethod
    def send_sms(cls, number, code, code_id, ip_addr: str = None, voice: bool = False, voice_code=None):
        if not BlockedIps.objects.filter(ip_address=ip_addr).exists():
            if SmsServices.objects.last().bird_message:
                try:
                    phone = settings.MESSAGE_BIRD_SERVICE_PHONE
                    auth_token = settings.MESSAGE_BIRD_SERVICE_TOKEN
                    sms = f'{code}'
                    if voice:
                        voice_message = 'Your verification code '
                        for i in str(voice_code):
                            voice_message += i + '  ' + '  ' + ' '
                        response = requests.post(
                            url=settings.MESSAGE_BIRD_SERVICE_URL_FOR_VOICE_SMS,
                            data={
                                'recipients': number,
                                'originator': phone,
                                'body': voice_message,
                                'repeat': 4,
                                'ifMachine': 'continue',
                                'machineTimeout': 400,
                                'language': 'en-us',
                                'voice': 'male'
                            },
                            headers={'Authorization': 'AccessKey ' + auth_token}
                        )
                    else:
                        response = requests.post(
                            url=settings.MESSAGE_BIRD_SERVICE_URL_FOR_SMS,
                            data={
                                'recipients': number,
                                'originator': phone,
                                'body': sms
                              },
                            headers={'Authorization': 'AccessKey ' + auth_token}
                        )
                    slack.bot(f'MessageBird\n{str(number)}\n {code}\n'
                              f'link code: https://apofiz.com/admin/users/temporarycode/{code_id}/change/\n'
                              f'ip: {ip_addr}\n'
                              f' status_code-{response.status_code}\n============================')
                except TwilioRestException as e:
                    slack.bot(f'MessageBird\n{str(number)}\n {code}\n'
                              f'ip: {ip_addr}\n'
                              f'( {e} )'
                              f'\n============================')
            else:
                slack.bot(f'MessageBird SERVICE IS OFF '
                          f'\n{str(number)}\n code -{code} code_id - {code_id}\n'
                          f'ip: {ip_addr}\n'
                          f'==============================')
        else:
            slack.bot(f'MessageBird SERVICE'
                      f'\n{str(number)}\n code -{code} code_id - {code_id}\n'
                      f'ip: {ip_addr}\n'
                      f'THIS IP IN BLACK LIST!!! \n'
                      f'==============================')

class MessageServiceTwilio:
    @classmethod
    def send_sms(cls, number, code, code_id, ip_addr: str = None):
        if not BlockedIps.objects.filter(ip_address=ip_addr).exists():
            if SmsServices.objects.last().twilio_service:
                try:
                    account_sid = settings.TWILIO_ACCOUNT_SID
                    auth_token = settings.TWILIO_AUTH_TOKEN
                    client = Client(account_sid, auth_token)
                    sms = f'{code}'

                    message = client.messages.create(
                        to=number,
                        from_=settings.TWILIO_SERVICE_SID,
                        body=sms)

                    slack.bot(f'TWILIO\n{str(number)}\n {code}\n'
                              f'link code: https://apofiz.com/admin/users/temporarycode/{code_id}/change/\n'
                              f'ip: {ip_addr}\n'
                              f' status_code-{message.status}\n============================')
                except TwilioRestException as e:
                    slack.bot(f'TWILIO\n{str(number)}\n {code}\n'
                              f'ip: {ip_addr}\n'
                              f'( {e} )'
                              f'\n============================')
            else:
                slack.bot(f'TWILIO SERVICE IS OFF '
                          f'\n{str(number)}\n code -{code} code_id - {code_id}\n'
                          f'ip: {ip_addr}\n'
                          f'==============================')
        else:
            slack.bot(f'TWILIO SERVICE'
                      f'\n{str(number)}\n code -{code} code_id - {code_id}\n'
                      f'ip: {ip_addr}\n'
                      f'THIS IP IN BLACK LIST!!! \n'
                      f'==============================')


    @classmethod
    def send_whatsapp_sms(cls, number, code, code_id):
        if SmsServices.objects.last().twilio_service:
            try:
                account_sid = settings.TWILIO_ACCOUNT_SID
                auth_token = settings.TWILIO_AUTH_TOKEN
                client = Client(account_sid, auth_token)
                sms = f'{code}'

                message = client.messages.create(
                    to=f'whatsapp:{number}',
                    from_=f'whatsapp:+14155238886',
                    body=sms)

                slack.bot(f'TWILIO\n{str(number)}\n {code}\n'
                          f'link code: https://apofiz.com/admin/users/temporarycode/{code_id}/change/\n'
                          f' status_code-{message.status}\n============================')
            except TwilioRestException as e:
                slack.bot(f'TWILIO\n{str(number)}\n {code}\n'
                          f'( {e} )'
                          f'\n============================')
        else:
            slack.bot(f'TWILIO SERVICE IS OFF '
                      f'\n{str(number)}\n code -{code} code_id - {code_id}\n'
                      f'\n==============================')


class AzamatMessageService:
    @classmethod
    def save_in_model(cls, message, phone_number):
        sms, created = SmsModel.objects.get_or_create(phone_number=phone_number, text=message)
