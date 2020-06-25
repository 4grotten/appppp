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
