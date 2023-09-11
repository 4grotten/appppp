from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from ..exceptions import NotAcceptableException
from ..models import OpenExchangeRates


class CurrencyConverterService:

    @classmethod
    def made_rate_request(cls, app_id, from_currency, to_currency):
        query = f'app_id={app_id}&symbols={from_currency},{to_currency}'
        response = requests.get(f'https://openexchangerates.org/api/latest.json?{query}')
        print("TY DALBI4?")
        if response.status_code != status.HTTP_200_OK:
            raise NotAcceptableException(_('Bad response from openexchangerates.org'))
        return response

    @classmethod
    def get_rate(cls, from_currency, to_currency):
        api_id = OpenExchangeRates.objects.last()

        if api_id:
            app_id = api_id.app_id
            response = cls.made_rate_request(app_id, from_currency=from_currency, to_currency=to_currency)
        else:
            app_id = settings.OER_APP_ID
            response = cls.made_rate_request(app_id, from_currency=from_currency, to_currency=to_currency)

        try:
            from_rate_to_base = response.json()['rates'][from_currency.upper()]
        except KeyError:
            raise NotAcceptableException(_('No currency with code %(currency)s') % {'currency': from_currency.upper()})
        print("from_rate_to_base", from_rate_to_base)
        cache.set(f'{settings.OER_BASE_CURRENCY}{from_currency}', from_rate_to_base, timeout=settings.OER_CACHE_TIMEOUT)
        print("CACHED!")
        try:
            to_rate_to_base = response.json()['rates'][to_currency.upper()]
        except KeyError:
            raise NotAcceptableException(_(f'No currency with code {to_currency.upper()}'))
        cache.set(f'{settings.OER_BASE_CURRENCY}{to_currency}', to_rate_to_base, timeout=settings.OER_CACHE_TIMEOUT)
        print("CACHED2!")

        rate = Decimal(to_rate_to_base) / Decimal(from_rate_to_base)
        cache.set(f'{from_currency}{to_currency}', rate, timeout=settings.OER_CACHE_TIMEOUT)
        print("CACHED3!")

        return rate

    @classmethod
    def get_rate_from_cache(cls, from_currency: str, to_currency: str):
        print("URA!")
        cached_exchange_rate = cache.get(f'{from_currency}{to_currency}')
        if cached_exchange_rate:
            return cached_exchange_rate

        reversed_exchange_rate = cache.get(f'{to_currency}{from_currency}')
        if reversed_exchange_rate:
            reversed_rate = Decimal(1.0) / Decimal(reversed_exchange_rate)
            cache.set(f'{from_currency}{to_currency}', reversed_rate, timeout=settings.OER_CACHE_TIMEOUT)
            return reversed_rate
        return None

    @classmethod
    def convert(cls, from_currency: str, to_currency: str, amount: Decimal) -> Decimal:
        if from_currency == to_currency:
            return amount
        exchange_rate = cls.get_rate_from_cache(from_currency, to_currency) or cls.get_rate(from_currency, to_currency)
        return round(Decimal(amount) * Decimal(exchange_rate), 6)
