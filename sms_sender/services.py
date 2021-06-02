import requests
from django.conf import settings
from django.template import Template, Context
from django.utils.translation import gettext_lazy as _


class MessageService:
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
