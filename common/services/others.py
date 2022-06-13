from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from common.models import LinkApp


class LinkAppService:
    @classmethod
    def get_link_app(cls, *args, **kwargs):
        try:
            return LinkApp.objects.last()
        except LinkApp.DoesNotExist:
            raise ObjectNotFoundException(_('LinkApp not found'))
