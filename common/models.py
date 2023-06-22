import os
import requests
import logging
from urllib import request
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.gis.db.models import PointField
from django.core.files import File as Files
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit import register
from imagekit.models import ImageSpecField

from common.constants import DEVICE_TYPES, MESSAGE_TYPE
from common.processors import ResizeWatermarkedSpec, MobileWallpaper
from common.utils import upload_file_with_unique_name, upload_file_video_with_unique_name
from django_resized import ResizedImageField



class LargeWatermarkedSpec(ResizeWatermarkedSpec):
    height = 600
    width = 600


class MediumWatermarkedSpec(ResizeWatermarkedSpec):
    height = 250
    width = 250


class SmallWatermarkedSpec(ResizeWatermarkedSpec):
    height = 150
    width = 150


register.generator('common:file:large', LargeWatermarkedSpec)
register.generator('common:file:medium', MediumWatermarkedSpec)
register.generator('common:file:small', SmallWatermarkedSpec)

register.generator('common:commentswallpaper:mobile', MobileWallpaper)


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class File(TimestampModel):
    is_watermarked = models.BooleanField(default=False, editable=False)
    order = models.PositiveSmallIntegerField(default=0, editable=False)

    file = models.ImageField(
        upload_to=upload_file_with_unique_name,
        help_text=_('Image that you want to store'),
        max_length=1000
    )

    image_url = models.URLField(null=True, blank=True, max_length=1000)

    large = ImageSpecField(source='file', id='common:file:large')
    medium = ImageSpecField(source='file', id='common:file:medium')
    small = ImageSpecField(source='file', id='common:file:small')

    @property
    def name(self):
        return self.file.name.split("/")[-1]

    @property
    def small_property(self):
        return self.small.url

    @property
    def medium_property(self):
        return self.medium.url

    @property
    def large_property(self):
        return self.large.url

    def __str__(self):  # pragma: no cover
        return self.file.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.image_url and not self.file:
            if self.image_url.startswith('https://renty.ae'):
                try:
                    response = requests.get(self.image_url)
                    img = Image.open(BytesIO(response.content))
                    img_io = BytesIO()
                    img.save(img_io, format='JPEG')
                    img_file = InMemoryUploadedFile(
                        img_io,
                        None,
                        os.path.basename(self.image_url),
                        'image/jpeg',
                        img_io.tell,
                        None
                    )
                    self.file = img_file
                except Exception as e:
                    logging.error(f"Error occurred during image retrieval: {str(e)}")
            elif "googleusercontent.com" in self.image_url:
                try:
                    from instagram_parsers.services.proxy_services import ProxyService
                    proxy = ProxyService.get_random_proxy_for_requests()
                    if not proxy:
                        proxy = []
                    print("IM HEREEEE, proxy:", proxy)
                    response = requests.get(self.image_url, proxies=proxy[0])
                    print("response", response)
                    img = Image.open(BytesIO(response.content))
                    img_io = BytesIO()
                    img.save(img_io, format='JPEG')
                    img_file = InMemoryUploadedFile(
                        img_io,
                        None,
                        os.path.basename(self.image_url),
                        'image/jpeg',
                        img_io.tell,
                        None
                    )
                    self.file = img_file
                except Exception as e:
                    logging.error(f"Error occurred during image retrieval: {str(e)}")
            else:
                counter = 0
                while counter <= 10:
                    try:
                        result = request.urlretrieve(self.image_url)
                        self.file.save(
                            os.path.basename(self.image_url),
                            Files(open(result[0], 'rb'))
                        )
                        break
                    except:
                        continue
        super(File, self).save()

    class Meta:
        ordering = ('order',)


class FileVideo(TimestampModel):
    order = models.PositiveSmallIntegerField(default=0, editable=False)

    thumbnail = models.ForeignKey(File, on_delete=models.CASCADE, related_name='file_videos', blank=True, null=True)
    video = models.FileField(
        upload_to=upload_file_video_with_unique_name,
        help_text=_('Image that you want to store'),
        max_length=1000
    )

    video_url = models.URLField(null=True, blank=True, max_length=1000)

    @property
    def name(self):
        return self.video.name.split("/")[-1]

    def __str__(self):  # pragma: no cover
        return self.video.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.video_url and not self.video:
            result = request.urlretrieve(self.video_url)
            self.video.save(
                os.path.basename(self.video_url),
                Files(open(result[0], 'rb'))
            )
        super(FileVideo, self).save()

    class Meta:
        ordering = ('order',)


class CommentsWallpaper(TimestampModel):
    web_image = models.ImageField(
        upload_to=upload_file_with_unique_name,
        help_text=_('Web wallpaper that you want to store'),
        max_length=1000
    )

    mobile_image = models.ImageField(
        upload_to=upload_file_with_unique_name,
        help_text=_('Mobile wallpaper that you want to store'),
        max_length=1000
    )
    is_active = models.BooleanField(default=True)
    mobile = ImageSpecField(source='mobile_image', id='common:commentswallpaper:mobile')

    @property
    def name(self):
        return self.web_image.name.split("/")[-1]

    @property
    def mobile_property(self):
        return self.mobile.url

    def __str__(self):  # pragma: no cover
        return self.web_image.name


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):  # pragma: no cover
        return f'{self.code}'

    class Meta:
        ordering = ('name',)
        verbose_name_plural = _('Currencies')


class Country(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50)
    flag = models.URLField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='countries')

    is_priority = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):  # pragma: no cover
        return f'{self.name}'

    class Meta:
        ordering = ('-is_priority', 'code',)
        verbose_name_plural = _('Countries')


class City(models.Model):
    name = models.CharField(max_length=50)
    postal = models.CharField(max_length=20, null=True, blank=True)
    location = PointField(null=True, blank=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):  # pragma: no cover
        return f'{self.name} in {self.country.name}'

    class Meta:
        ordering = ('name', 'country',)
        verbose_name_plural = _('Cities')


class Version(TimestampModel):
    device = models.CharField(max_length=255, choices=DEVICE_TYPES, unique=True)
    version = models.CharField(max_length=255)
    force_update = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.device}- {self.version}'

    class Meta:
        verbose_name = _('Version')
        verbose_name_plural = _('Versions')


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)


class OpenExchangeRates(TimestampModel, SingletonModel):
    app_id = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.app_id}- {self.created_at} - {self.updated_at}'

    class Meta:
        verbose_name = _('id for exchange service')
        verbose_name_plural = _('id for exchange services')


class LinkApp(SingletonModel):
    name_link = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name_link}'


class Languages(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    language_en = models.CharField(max_length=255)
    language_ru = models.CharField(max_length=255)
    national_language = models.CharField(max_length=255)
    flag = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True, related_name='language')

    def __str__(self):
        return f'{self.flag} - {self.code} - {self.language_ru} - {self.national_language}'

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ('code',)


class UmaiWallet(TimestampModel, SingletonModel):
    wallet = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    amount = models.SmallIntegerField(validators=[MinValueValidator(2), MaxValueValidator(1000)], default=50)
    activate = models.BooleanField(default=True)
    version = models.CharField(max_length=255, blank=True, null=True, default='2.14.8')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.id}-{self.amount}'

    @property
    def is_accepted(self):
        if self.activate and self.start_time <= timezone.now() <= self.end_time:
            return True
        return False

    class Meta:
        verbose_name = _('Registration payment')
        verbose_name_plural = _('Registration payments')


class MessageText(TimestampModel):
    name = models.CharField(max_length=255, unique=True, verbose_name=_('Message name, unique'), help_text=_('*unique'))
    body = models.TextField(max_length=2000, verbose_name=_('Message text'))
    message_type = models.CharField(max_length=255, choices=MESSAGE_TYPE, verbose_name=_('message type'))

    def __str__(self):
        return f'{self.id}- {self.name}'

    class Meta:
        verbose_name = _('Message text')
        verbose_name_plural = _('Messages Text')


class SmsServices(SingletonModel):
    twilio_service = models.BooleanField(verbose_name=_('Twilio service'), default=True)
    nikita_service = models.BooleanField(verbose_name=_('Nikita Service'), default=True)
    bird_message = models.BooleanField(verbose_name=_('Bird message Service'), default=True)

    def __str__(self):
        return f'Twilio: {self.twilio_service}| Nikita: {self.nikita_service}'

    class Meta:
        verbose_name = _('Sms service')
        verbose_name_plural = _('Sms services')


class TemporaryCodeSwitcher(SingletonModel):
    is_enable = models.BooleanField(verbose_name=_("Enable"), default=True)

    def __str__(self):
        return f'{self.is_enable}'

    class Meta:
        verbose_name = _('Temporary code switcher')


class BlockedIps(TimestampModel):
    ip_address = models.CharField(max_length=255, verbose_name=_('Blocked ip'))

    def __str__(self):
        return f'{self.id} - IP:{self.ip_address}'

    class Meta:
        verbose_name = _('IP address')
        verbose_name_plural = _('IP addresses')