import datetime
import uuid

from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

from django.db import models
from common.models import TimestampModel
from common.utils import generate_random_code
from .constants import GENDER_CHOICES
from .managers import UserManager


class User(AbstractUser, TimestampModel):
    first_name = models.CharField(max_length=255, verbose_name='First Name', null=True, blank=True)
    last_name = models.CharField(max_length=255, verbose_name='Last Name', null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name='Full Name', null=True, blank=True)
    email = models.EmailField(verbose_name='Email', unique=True)
    phone_number = PhoneNumberField(unique=True, max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    avatar = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    is_new_user = models.BooleanField(default=True)
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return str(self.phone_number)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.email = "{}@example.com".format(uuid.uuid4().hex[:6].upper())
        super(User, self).save(*args, **kwargs)


class TemporaryCode(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.IntegerField(blank=True)
    is_used = models.BooleanField(default=False)
    expiration_datetime = models.DateTimeField(blank=True)

    def __str__(self):
        return str(self.user.phone_number)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = generate_random_code()
            self.expiration_datetime = datetime.datetime.now() + datetime.timedelta(minutes=2)
        super(TemporaryCode, self).save(*args, **kwargs)


class TemporaryPhoneNumber(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=255)
    code = models.IntegerField(blank=True)
    expiration_datetime = models.DateTimeField(blank=True)

    def __str__(self):
        return self.user.phone_number

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = generate_random_code()
            self.expiration_datetime = datetime.datetime.now() + datetime.timedelta(minutes=2)
        super(TemporaryPhoneNumber, self).save(*args, **kwargs)


class PhoneNumber(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return self.phone_number


class SocialNetworkContact(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_contacts')
    url = models.CharField(max_length=255)

    def __str__(self):
        return self.url
