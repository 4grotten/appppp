from django.db import models
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFit

from common.utils import upload_file_with_original_file_name


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class File(TimestampModel):
    file = models.ImageField(
        upload_to=upload_file_with_original_file_name,
        help_text='Image that you want to store'
    )

    large = ImageSpecField(source='file',
                           processors=[ResizeToFit(600, 600, upscale=False)],
                           format='JPEG',
                           options={'quality': 100})
    medium = ImageSpecField(source='file',
                            processors=[ResizeToFit(150, 150, upscale=False)],
                            format='JPEG',
                            options={'quality': 100})
    small = ImageSpecField(source='file',
                           processors=[ResizeToFit(50, 50, upscale=False)],
                           format='JPEG',
                           options={'quality': 100})

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
