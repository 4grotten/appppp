from django.contrib.gis.db.models import PointField
from django.db import models
from imagekit import register
from imagekit.models import ImageSpecField

from common.processors import ResizeWatermarkedSpec
from common.utils import upload_file_with_original_file_name


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
        upload_to=upload_file_with_original_file_name,
        help_text='Image that you want to store'
    )

    large = ImageSpecField(source='file', id='common:file:large')
    medium = ImageSpecField(source='file', id='common:file:medium')
    small = ImageSpecField(source='file', id='common:file:small')

    def __str__(self):
        return self.file.name

    class Meta:
        ordering = ('order',)


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f'{self.code}'

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Currencies'


class Country(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50)
    flag = models.URLField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='countries')

    is_priority = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        ordering = ('-is_priority', 'code',)
        verbose_name_plural = 'Countries'


class City(models.Model):
    name = models.CharField(max_length=50)
    postal = models.CharField(max_length=20, null=True, blank=True)
    location = PointField(null=True, blank=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return f'{self.name} in {self.country.name}'

    class Meta:
        ordering = ('name', 'country',)
        verbose_name_plural = 'Cities'
