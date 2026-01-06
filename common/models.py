import logging
import os
from io import BytesIO
from urllib import request

import requests
from django.contrib.gis.db.models import PointField
from django.core.files import File as Files
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit import register
from imagekit.models import ImageSpecField
from PIL import Image

from common.constants import DEVICE_TYPES, MESSAGE_TYPE
from common.processors import MobileWallpaper, ResizeWatermarkedSpec
from common.utils import (
    upload_file_video_with_unique_name,
    upload_file_with_unique_name,
)


class LargeWatermarkedSpec(ResizeWatermarkedSpec):
    height = 600
    width = 600


class MediumWatermarkedSpec(ResizeWatermarkedSpec):
    height = 250
    width = 250


class SmallWatermarkedSpec(ResizeWatermarkedSpec):
    height = 150
    width = 150


register.generator("common:file:large", LargeWatermarkedSpec)
register.generator("common:file:medium", MediumWatermarkedSpec)
register.generator("common:file:small", SmallWatermarkedSpec)

register.generator("common:commentswallpaper:mobile", MobileWallpaper)


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
        help_text=_("Image that you want to store"),
        max_length=1000,
    )

    image_url = models.URLField(null=True, blank=True, max_length=1000)

    large = ImageSpecField(source="file", id="common:file:large")
    medium = ImageSpecField(source="file", id="common:file:medium")
    small = ImageSpecField(source="file", id="common:file:small")

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

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.image_url and not self.file:
            if (
                self.image_url.startswith("https://renty.ae")
                or self.image_url.startswith("https://avacarrental.com/")
                or ".2gis.com" in self.image_url
            ):
                try:
                    response = requests.get(self.image_url)
                    img = Image.open(BytesIO(response.content))
                    if img.mode == "RGBA":
                        img = img.convert("RGB")
                    img_io = BytesIO()
                    img.save(img_io, format="JPEG")
                    img_file = InMemoryUploadedFile(
                        img_io,
                        None,
                        os.path.basename(self.image_url),
                        "image/jpeg",
                        img_io.tell,
                        None,
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
                            Files(open(result[0], "rb")),
                        )
                        break
                    except:
                        continue
        super(File, self).save()

    class Meta:
        ordering = ("order",)


class FileVideo(TimestampModel):
    order = models.PositiveSmallIntegerField(default=0, editable=False)

    thumbnail = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="file_videos",
        blank=True,
        null=True,
    )
    video = models.FileField(
        upload_to=upload_file_video_with_unique_name,
        help_text=_("Image that you want to store"),
        max_length=1000,
    )

    video_url = models.URLField(null=True, blank=True, max_length=1000)

    @property
    def name(self):
        return self.video.name.split("/")[-1]

    def __str__(self):  # pragma: no cover
        return self.video.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.video_url and not self.video:
            result = request.urlretrieve(self.video_url)
            self.video.save(
                os.path.basename(self.video_url), Files(open(result[0], "rb"))
            )
        super(FileVideo, self).save()

    class Meta:
        ordering = ("order",)


class CommentsWallpaper(TimestampModel):
    web_image = models.ImageField(
        upload_to=upload_file_with_unique_name,
        help_text=_("Web wallpaper that you want to store"),
        max_length=1000,
    )

    mobile_image = models.ImageField(
        upload_to=upload_file_with_unique_name,
        help_text=_("Mobile wallpaper that you want to store"),
        max_length=1000,
    )
    is_active = models.BooleanField(default=True)
    mobile = ImageSpecField(source="mobile_image", id="common:commentswallpaper:mobile")

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
        return f"{self.code}"

    class Meta:
        ordering = ("name",)
        verbose_name_plural = _("Currencies")


class Country(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=255)
    currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE, related_name="countries"
    )

    is_priority = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_paid_subscription = models.BooleanField(
        default=False, verbose_name="Платная подписка"
    )

    def __str__(self):  # pragma: no cover
        return f"{self.name}"

    class Meta:
        ordering = (
            "-is_priority",
            "code",
        )
        verbose_name_plural = _("Countries")


class City(models.Model):
    name = models.CharField(max_length=50)
    postal = models.CharField(max_length=20, null=True, blank=True)
    location = PointField(null=True, blank=True)

    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="cities"
    )

    timezone = models.CharField(max_length=64, default="UTC")

    def __str__(self):  # pragma: no cover
        return f"{self.name} in {self.country.name}"

    class Meta:
        ordering = (
            "name",
            "country",
        )
        verbose_name_plural = _("Cities")


class Version(TimestampModel):
    device = models.CharField(max_length=255, choices=DEVICE_TYPES, unique=True)
    version = models.CharField(max_length=255)
    force_update = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.device}- {self.version}"

    class Meta:
        verbose_name = _("Version")
        verbose_name_plural = _("Versions")


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)


class OpenExchangeRates(TimestampModel, SingletonModel):
    app_id = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.app_id}- {self.created_at} - {self.updated_at}"

    class Meta:
        verbose_name = _("id for exchange service")
        verbose_name_plural = _("id for exchange services")


class LinkApp(SingletonModel):
    name_link = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name_link}"


class Languages(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    language_en = models.CharField(max_length=255)
    language_ru = models.CharField(max_length=255)
    national_language = models.CharField(max_length=255)
    flag = models.ForeignKey(
        "common.File",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="language",
    )

    def __str__(self):
        return (
            f"{self.flag} - {self.code} - {self.language_ru} - {self.national_language}"
        )

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ("code",)


class UmaiWallet(TimestampModel, SingletonModel):
    wallet = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    amount = models.SmallIntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(1000)], default=50
    )
    activate = models.BooleanField(default=True)
    version = models.CharField(max_length=255, blank=True, null=True, default="2.14.8")
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}-{self.amount}"

    @property
    def is_accepted(self):
        if self.activate and self.start_time and self.end_time:
            if self.start_time <= timezone.now() <= self.end_time:
                return True
        return False

    class Meta:
        verbose_name = _("Registration payment")
        verbose_name_plural = _("Registration payments")


class MessageText(TimestampModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Message name, unique"),
        help_text=_("*unique"),
    )
    body = models.TextField(max_length=2000, verbose_name=_("Message text"))
    message_type = models.CharField(
        max_length=255, choices=MESSAGE_TYPE, verbose_name=_("message type")
    )

    def __str__(self):
        return f"{self.id}- {self.name}"

    class Meta:
        verbose_name = _("Message text")
        verbose_name_plural = _("Messages Text")


class SmsServices(SingletonModel):
    twilio_service = models.BooleanField(verbose_name=_("Twilio service"), default=True)
    nikita_service = models.BooleanField(verbose_name=_("Nikita Service"), default=True)
    bird_message = models.BooleanField(
        verbose_name=_("Bird message Service"), default=True
    )

    def __str__(self):
        return f"Twilio: {self.twilio_service}| Nikita: {self.nikita_service}"

    class Meta:
        verbose_name = _("Sms service")
        verbose_name_plural = _("Sms services")


class TemporaryCodeSwitcher(SingletonModel):
    is_enable = models.BooleanField(verbose_name=_("Enable"), default=True)

    def __str__(self):
        return f"{self.is_enable}"

    class Meta:
        verbose_name = _("Temporary code switcher")


class BlockedIps(TimestampModel):
    ip_address = models.CharField(max_length=255, verbose_name=_("Blocked ip"))

    def __str__(self):
        return f"{self.id} - IP:{self.ip_address}"

    class Meta:
        verbose_name = _("IP address")
        verbose_name_plural = _("IP addresses")


class CountryInvoiceInfo(TimestampModel):
    country = models.OneToOneField(
        Country, on_delete=models.CASCADE, related_name="invoice_info"
    )
    tax = models.PositiveIntegerField(default=0, null=True, blank=True)
    tax_id = models.CharField(max_length=255, default="", null=True, blank=True)
    name = models.CharField(max_length=455)
    city = models.CharField(max_length=255, default="")
    address = models.CharField(max_length=455)
    email = models.EmailField()
    bank_details = models.TextField(default="")


class ChatGPTSettings(TimestampModel, SingletonModel):
    """
    Singleton model для хранения настроек ChatGPT API.
    Позволяет динамически менять API ключ через админку.
    """
    api_key = models.CharField(
        max_length=255,
        verbose_name=_("OpenAI API Key"),
        help_text=_("API ключ для доступа к ChatGPT. Формат: sk-proj-...")
    )
    model = models.CharField(
        max_length=50,
        default="gpt-3.5-turbo",
        verbose_name=_("Модель GPT"),
        help_text=_("Модель для использования (gpt-3.5-turbo, gpt-4, gpt-4o-mini и т.д.)")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен"),
        help_text=_("Включить/выключить интеграцию с ChatGPT")
    )
    temperature = models.FloatField(
        default=0.9,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        verbose_name=_("Temperature"),
        help_text=_("Уровень креативности ответов (0.0 - 2.0)")
    )
    max_tokens = models.PositiveIntegerField(
        default=500,
        validators=[MinValueValidator(50), MaxValueValidator(4000)],
        verbose_name=_("Max Tokens"),
        help_text=_("Максимальное количество токенов в ответе (50-4000). 500 токенов ≈ 350-400 слов")
    )
    min_sentences = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name=_("Мин. предложений"),
        help_text=_("Минимальное количество предложений в описании")
    )
    max_sentences = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        verbose_name=_("Макс. предложений"),
        help_text=_("Максимальное количество предложений в описании")
    )
    min_words = models.PositiveIntegerField(
        default=150,
        validators=[MinValueValidator(20), MaxValueValidator(1000)],
        verbose_name=_("Мин. слов"),
        help_text=_("Примерное минимальное количество слов в описании")
    )
    max_words = models.PositiveIntegerField(
        default=250,
        validators=[MinValueValidator(50), MaxValueValidator(2000)],
        verbose_name=_("Макс. слов"),
        help_text=_("Примерное максимальное количество слов в описании")
    )

    def __str__(self):
        return f"ChatGPT Settings (Active: {self.is_active})"

    @classmethod
    def get_settings(cls):
        """Получить настройки ChatGPT. Создает запись по умолчанию, если её нет."""
        settings, created = cls.objects.get_or_create(
            defaults={
                'api_key': '',
                'model': 'gpt-3.5-turbo',
                'is_active': True,
                'temperature': 0.9,
                'max_tokens': 500,
                'min_sentences': 6,
                'max_sentences': 10,
                'min_words': 150,
                'max_words': 250,
            }
        )
        return settings

    @classmethod
    def get_api_key(cls):
        """Получить API ключ."""
        settings = cls.get_settings()
        return settings.api_key if settings.is_active else None

    class Meta:
        verbose_name = _("ChatGPT Settings")
        verbose_name_plural = _("ChatGPT Settings")
