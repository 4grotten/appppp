from django.contrib.auth import get_user_model
from django.db import models

from common.models import File, TimestampModel


class OrganizationsImportFile(TimestampModel):
    user = models.ForeignKey(get_user_model(), blank=True, related_name='organizations_import_files', editable=False, null=True, on_delete=models.SET_NULL)
    file = models.FileField(null=True)
    phone_number = models.CharField(max_length=255)
    num_rows = models.IntegerField(null=True, blank=True, editable=False)

    def __str__(self):
        return f"{self.user}-{self.phone_number}"
