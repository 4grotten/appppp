import json

from django.conf import settings
import requests


def bot(message):
    slack_token = settings.SLACK_TOKEN
    slack_url = 'https://slack.com/api/chat.postMessage'
    channel = "C02KEV49PPE"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {slack_token}'
    }

    data = {
        "channel": f"{channel}",
        "text": f"{message}"
    }
    data = json.dumps(data)
    requests.post(url=slack_url, data=data, headers=headers)


def bot_2(message):
    slack_token = settings.SLACK_TOKEN
    slack_url = 'https://slack.com/api/chat.postMessage'
    channel = "C03CFMZDZ1B"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {slack_token}'
    }

    data = {
        "channel": f"{channel}",
        "text": f"{message}"
    }
    data = json.dumps(data)
    requests.post(url=slack_url, data=data, headers=headers)
