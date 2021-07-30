from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import Version


class VersionService:
    @classmethod
    def get(cls,  *args, **kwargs):
        try:
            return Version.objects.get(*args, **kwargs)
        except Version.DoesNotExist:
            raise ObjectNotFoundException(_('Version not found'))
