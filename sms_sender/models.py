from django.db import models

from common.models import TimestampModel


class SmsModel(TimestampModel):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILURE = 'failure'
    STATUS = (
        (PENDING, PENDING),
        (SUCCESS, SUCCESS),
        (FAILURE, FAILURE),
    )

    phone_number = models.CharField(max_length=255, unique=True)
    text = models.TextField(null=True, blank=True, max_length=500)
    status = models.CharField(max_length=20, choices=STATUS, null=True, blank=True)

    def __str__(self):
        return f'{self.phone_number}'
