from django.contrib.auth.models import AbstractUser

from django.db import models

from common.models import TimestampModel
from .managers import UserManager


class User(AbstractUser, TimestampModel):
    first_name = models.CharField(max_length=255, verbose_name='First Name')
    last_name = models.CharField(max_length=255, verbose_name='Last Name')
    email = models.EmailField(verbose_name='Email', unique=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)

    # TODO add role, avatar fields

    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return "{first_name} {last_name}".format(first_name=self.first_name, last_name=self.last_name)
