from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from stock.models import FormatCriteria, SizeFormat


class FormatSizeService:
    model = FormatCriteria

    @classmethod
    def get_format_of_criteria(cls):
        return cls.model.objects.all()


class SizeFormatService:
    model = SizeFormat

    @classmethod
    def get_sizes_by_format_id(cls, format_criteria_id):
        return cls.model.objects.select_related('format_criteria').filter(format_criteria__id=format_criteria_id).order_by('order')
