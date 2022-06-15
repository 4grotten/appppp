from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from stock.models import FormatSize, ShopItemSize


class FormatSizeService:
    model = FormatSize

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Notification not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get_format_sizes(cls):
        return cls.model.objects.all()


class ShopItemSizeService:
    model = ShopItemSize

    @classmethod
    def get_sizes_by_format_id(cls, format_size_id):
        return cls.model.objects.select_related('format_size').filter(format_size__id=format_size_id).order_by('order')
