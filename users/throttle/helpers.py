import requests
from rest_framework.exceptions import PermissionDenied

from project.settings.base import RE_CAPTCHA_SECRET_KEY


def verify_recaptcha(g_token: str) -> bool:
    data = {
        'response': g_token,
        'secret': RE_CAPTCHA_SECRET_KEY

    }
    resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result_json = resp.json()
    if result_json.get('success') is False:
        raise PermissionDenied("Forbidden")
    return result_json.get('success') is True
