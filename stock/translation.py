from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from stock.models import FormatSize


@register(FormatSize)
class FormatSizeOptions(TranslationOptions):
    fields = (
        'name',
    )
