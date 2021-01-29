from django.urls import reverse
from rest_framework.test import APITestCase


class CountrySearchTestCase(APITestCase):
    def setUp(self):
        self.countries = reverse('v1:countries')
        self.countries_cities_search = reverse('v1:countries_cities_search')

    def test_countries_cities_search_view(self):

        response = self.client.get(self.countries_cities_search)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['overall_total'], 237)

    def test_countries_cities_search_view_keyword(self):
        response = self.client.get(self.countries_cities_search, data={'search': 'кыргызстан'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['overall_total'], 1)
        self.assertEqual(response.data['results']['countries'][0]['name'], 'Kyrgyzstan')
