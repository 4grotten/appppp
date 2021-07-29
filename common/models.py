import os
from urllib import request

from django.contrib.gis.db.models import PointField
from django.core.files import File as Files
from django.db import models
from django.utils.translation import gettext_lazy as _
from imagekit import register
from imagekit.models import ImageSpecField

from common.constants import DEVICE_TYPES
from common.processors import ResizeWatermarkedSpec
from common.utils import upload_file_with_unique_name


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

    def __str__(self):  # pragma: no cover
        return self.file.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.image_url and not self.file:
            result = request.urlretrieve(self.image_url)
            self.file.save(
                os.path.basename(self.image_url),
                Files(open(result[0], 'rb'))
            )
        super(File, self).save()

    class Meta:
        ordering = ('order',)


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
    device = models.CharField(max_length=255, choices=DEVICE_TYPES)
    version = models.CharField(max_length=255)
    required_to_update = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.device}- {self.version}'

    class Meta:
        verbose_name = _('Version')
        verbose_name_plural = _('Versions')
