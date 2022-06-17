from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from stock.models import FormatCriteria, CriteriaSubcategory


@register(CriteriaSubcategory)
class CriteriaSubcategoryOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(FormatCriteria)
class FormatSizeOptions(TranslationOptions):
    fields = (
        'name',
    )
