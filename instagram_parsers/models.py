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
    proxy_http_s = models.CharField(null=True, blank=True, max_length=25, help_text=_('Example : 91.238.224.165:20196'))
    proxy_socks5 = models.CharField(null=True, blank=True, max_length=25, help_text=_('Example : 91.238.224.165:20196'))
    proxy_login = models.CharField(max_length=255, null=True)
    proxy_password = models.CharField(max_length=255, null=True)
    proxy_expires_at = models.DateTimeField(null=True, blank=True)
    is_broke = models.BooleanField(default=False, help_text='This login_device broke, please update settings')

    def __str__(self):
        return f'{self.updated_at.date()}'


class InstagramApi(TimestampModel):
    username = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    proxy = models.ForeignKey(Proxy, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=False, help_text='This instagram_api non active, please update settings')

    def __str__(self):
        return f'{self.username}'

    def save(self, *args, **kwargs):
        if self.is_active:
            InstagramApi.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)
