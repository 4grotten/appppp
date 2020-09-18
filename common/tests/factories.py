import factory

from common.models import Currency


class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Currency
