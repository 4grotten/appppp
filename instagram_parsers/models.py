from django.db import models
from common.models import TimestampModel


class Proxy(TimestampModel):
    http_s = models.CharField(null=True, blank=True, max_length=25)
    socks5 = models.CharField(null=True, blank=True, max_length=25)
    login = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.login}'
