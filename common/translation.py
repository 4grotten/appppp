from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register

from .models import Country, City, Currency, MessageText


@register(MessageText)
class MessageTextOptions(TranslationOptions):
    fields = (
        'name',
        'body',
    )


@register(Country)
class CountryOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(City)
class CityOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(Currency)
class CurrencyOptions(TranslationOptions):
    fields = (
        'name',
    )
