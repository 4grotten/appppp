from django.test import TestCase
from unittest.mock import patch, Mock
import requests_mock

from common.services.currency import CurrencyConverterService
from common.exceptions import NotAcceptableException
from decimal import Decimal

from django.core.cache import cache
from django.conf import settings


class TestServiceCurrency(TestCase):
    def setUp(self):
        self.kgs = 83.93884
        self.usd = 1
        self.rate = Decimal(self.kgs) / Decimal(self.usd)
        self.answer = {
            'base': 'USD',
            'disclaimer': 'Usage subject to terms: https://openexchangerates.org/terms',
            'license': 'https://openexchangerates.org/license',
            'rates': {
                'KGS': self.kgs,
                'USD': self.usd
            },
            'timestamp': 1611932360
        }

    @requests_mock.Mocker()
    def test_request_for_get_rate(self, requests):

        requests.get(
            requests_mock.ANY,
            json=self.answer
        )

        rate = CurrencyConverterService.get_rate('USD', 'KGS')

        self.assertTrue(requests.called)
        self.assertEqual(requests.last_request.hostname, 'openexchangerates.org')
        self.assertEqual(requests.last_request.path, '/api/latest.json')
        self.assertListEqual(requests.last_request.qs['symbols'], ['usd,kgs'])

        self.assertEqual(rate, self.rate)

        self.assertAlmostEqual(cache.get(f'{settings.OER_BASE_CURRENCY}USD'), Decimal(self.usd))
        self.assertAlmostEqual(cache.get(f'{settings.OER_BASE_CURRENCY}KGS'), Decimal(self.kgs))

    @requests_mock.Mocker()
    def test_request_for_get_rate_invalid_http_code(self, requests):
        requests.get(
            requests_mock.ANY,
            status_code=404
        )

        with self.assertRaisesRegex(NotAcceptableException, 'Bad response from openexchangerates.org'):
            CurrencyConverterService.get_rate('USD', 'KGS')

        self.assertTrue(requests.called)
        self.assertEqual(requests.last_request.hostname, 'openexchangerates.org')
        self.assertEqual(requests.last_request.path, '/api/latest.json')

    @requests_mock.Mocker()
    def test_request_for_get_rate_invalid_from_currency(self, requests):
        q = self.answer.copy()

        q['rates'].pop('USD')

        requests.get(
            requests_mock.ANY,
            json=q
        )

        with self.assertRaisesRegex(NotAcceptableException, 'No currency with code USD'):
            CurrencyConverterService.get_rate('USD', 'KGS')

        self.assertTrue(requests.called)
        self.assertEqual(requests.last_request.hostname, 'openexchangerates.org')
        self.assertEqual(requests.last_request.path, '/api/latest.json')

    @requests_mock.Mocker()
    def test_request_for_get_rate_invalid_to_currency(self, requests):
        q = self.answer.copy()

        q['rates'].pop('KGS')

        requests.get(
            requests_mock.ANY,
            json=q
        )

        with self.assertRaisesRegex(NotAcceptableException, 'No currency with code KGS'):
            CurrencyConverterService.get_rate('USD', 'KGS')

        self.assertTrue(requests.called)
        self.assertEqual(requests.last_request.hostname, 'openexchangerates.org')
        self.assertEqual(requests.last_request.path, '/api/latest.json')

    def test_cache_currency_get_in_cache(self):

        cache.set('USDKGS', Decimal(123.456))

        self.assertAlmostEqual(CurrencyConverterService.get_rate_from_cache('USD', 'KGS'), Decimal(123.456))
        self.assertAlmostEqual(CurrencyConverterService.get_rate_from_cache('KGS', 'USD'), Decimal(1) / Decimal(123.456))

    def test_cache_currency_get_not_in_cache(self):
        self.assertIsNone(CurrencyConverterService.get_rate_from_cache('EUR', 'KGS'))

    def test_convert_from_equal_currencies(self):
        self.assertEqual(CurrencyConverterService.convert('KGS', 'KGS', Decimal(123.456)), Decimal(123.456))

    @patch('common.services.currency.CurrencyConverterService.get_rate_from_cache', return_value=Decimal(654.321))
    @patch('common.services.currency.CurrencyConverterService.get_rate')
    def test_convert_in_cache(self, mock_get: Mock, mock_from_cache: Mock):
        self.assertEqual(
            CurrencyConverterService.convert('ABC', 'DEF', Decimal(123.456)),
            round(Decimal(123.456) * Decimal(654.321), 6)
        )

        mock_from_cache.assert_called()
        mock_from_cache.assert_called_with('ABC', 'DEF')

        mock_get.assert_not_called()

    @patch('common.services.currency.CurrencyConverterService.get_rate_from_cache', return_value=None)
    @patch('common.services.currency.CurrencyConverterService.get_rate', return_value=Decimal(654.321))
    def test_convert_in_get_request(self, mock_get: Mock, mock_from_cache: Mock):
        self.assertEqual(
            CurrencyConverterService.convert('ABC', 'DEF', Decimal(123.456)),
            round(Decimal(123.456) * Decimal(654.321), 6)
        )

        mock_from_cache.assert_called_with('ABC', 'DEF')
        mock_get.assert_called_with('ABC', 'DEF')
