from django.contrib.gis.db.models import PointField
from django.db import models
from imagekit.models import ImageSpecField

from common.utils import upload_file_with_original_file_name


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class File(TimestampModel):
    is_watermarked = models.BooleanField(default=False)

    file = models.ImageField(
        upload_to=upload_file_with_original_file_name,
        help_text='Image that you want to store'
    )

    large = ImageSpecField(source='file', id='large_watermark_image_spec')
    medium = ImageSpecField(source='file', id='medium_watermark_image_spec')
    small = ImageSpecField(source='file', id='small_watermark_image_spec')

    def __str__(self):
        return self.file.name


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
