from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampModel


class Proxy(TimestampModel):
    http_s = models.CharField(null=True, blank=True, max_length=25, help_text=_('Example : 91.238.224.165:20196'))
    socks5 = models.CharField(null=True, blank=True, max_length=25, help_text=_('Example : 91.238.224.165:20196'))
    login = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    for_getting_username = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.login}'


class LoginDevice(TimestampModel):
    for_getting_username = models.BooleanField(default=False)
    settings = models.JSONField(null=False, blank=True)
    username = models.CharField(max_length=255, default='nikabenod')
    password = models.CharField(max_length=255, default='1234qwer/')

    def __str__(self):
        return f'{self.updated_at.date()}'
