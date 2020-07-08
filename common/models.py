from django.db import models

from common.utils import upload_file_with_original_file_name


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class File(TimestampModel):
    file = models.FileField(
        upload_to=upload_file_with_original_file_name,
        help_text='File that you want to store'
    )

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
