import re, json
import requests

from typing import List
from django.conf import settings
from urllib.parse import urljoin
from rest_framework.exceptions import ValidationError
from instagram_parsers.services.proxy_services import ProxyService


class GoogleMapsService:
    @classmethod
    def get_api_key(cls, *args, **kwargs):
        api_key = settings.GOOGLE_MAP_API_KEY
        return api_key

    @classmethod
    def get_place_CID(cls, gMaps_URL):
        try:
            response = requests.get(gMaps_URL)
            text = response.url
            pattern = r'(?::|tid=)(0x[a-z0-9]+)(?:!|&hl=|\?utm_source=)'
            match = re.search(pattern, text)
            if match:
                cid_hexadecimal = match.group(1)
                cid = str(int(cid_hexadecimal, 16))
                return cid
        except Exception as e:
            error_data = {
                "message": "Invalid input",
                "errors": {
                    "google_maps_url": [
                        "Enter a valid URL."
                    ]
                }
            }
            raise ValidationError(error_data)


    @classmethod
    def get_place_details(cls, gMaps_URL: str):
        api_key = cls.get_api_key()

        cid = cls.get_place_CID(gMaps_URL)
        lang = '&language=ru'  # язык в котором будет json
        details_url = f'https://maps.googleapis.com/maps/api/place/details/json?cid={cid}&key={api_key}{lang}'
        r = requests.get(details_url)
        place_details = r.json()
        return place_details['result']

    @classmethod
    def get_image_ID(cls, photo_reference: str, request):
        api_key = cls.get_api_key()
        r = requests.get(f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={api_key}")
        place_image = r.url

        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version


        URL_IMAGE_ENDPOINT = urljoin(base_url, 'save_image_from_url/')

        query = {
            'image_url': place_image,
            'is_watermarked': True
        }
        token = request.headers.get('Authorization')
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r_image_headers = {'Authorization': token, 'Accept-Language': 'ru'}
        try:
            r_image = requests.post(url=URL_IMAGE_ENDPOINT, headers=r_image_headers, data=query, proxies=proxy[0])
            json_data = json.loads(r_image.text)
            image_ID = json_data['id']

            return image_ID
        except Exception as e:
            error_data = {
                "message": "Invalid input",
                "errors": {
                    "google_maps_url": [
                        "Enter a valid URL."
                    ]
                }
            }
            raise ValidationError(error_data)

    @classmethod
    def get_curency_CODE(cls, gMaps_country_short_name, request) -> str:
        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_COUNTRIES_AND_CITIES = urljoin(base_url, 'countries_and_cities/?limit=240')
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_COUNTRIES_AND_CITIES, proxies=proxy[0])
        for country in r.json()['results']['countries']:
            if country['code'] == gMaps_country_short_name:
                return country['currency']['code']

    @classmethod
    def get_country_CODE(cls, gMaps_country_short_name, request) -> str:
        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_COUNTRIES_AND_CITIES = urljoin(base_url, 'countries_and_cities/?limit=240')
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_COUNTRIES_AND_CITIES, proxies=proxy[0])
        for country in r.json()['results']['countries']:
            if country['code'] == gMaps_country_short_name:
                return country['code']

    @classmethod
    def get_city_ID(cls, sity_name, request):
        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_COUNTRIES_AND_CITIES = urljoin(base_url, f'countries_and_cities/?search={sity_name}')
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_COUNTRIES_AND_CITIES, proxies=proxy[0])
        results = r.json().get('results', {})

        cities = results.get('cities', [])
        if cities:
            city_id = cities[0]['id']
            return city_id
        else:
            return None

    @classmethod
    def get_place_type_ID(cls, place_type, request):
        token = request.headers.get('Authorization')
        _headers = {'Authorization': token, 'Accept-Language': 'ru'}

        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_ORGANIZATION_TYPES = urljoin(base_url, f'organization_all_types/?search={place_type}')
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_ORGANIZATION_TYPES, headers=_headers, proxies=proxy[0])
        if r.json() == []:
            return None
        else:
            for item in r.json():
                if item['title'] == place_type:
                    organization_type_ID = item['id']
                    return organization_type_ID
    @classmethod
    def add_organization(cls, gMaps_URL: str, request):
        data = cls.get_place_details(gMaps_URL)

        apofiz_add_organization = {}

        apofiz_add_organization['title'] = data['name']
        photo_reference = data['photos'][0]['photo_reference']
        image_id = cls.get_image_ID(photo_reference, request)
        if image_id == 'Учетные данные не были предоставлены.':
            apofiz_add_organization[
                'image_id'] = 57323  # default geocode result icon из гугл карт на случай ошибки с картинкой
        else:
            apofiz_add_organization['image_id'] = image_id
        try:
            apofiz_add_organization['description'] = data['editorial_summary']['overview']
        except:
            apofiz_add_organization['description'] = ''
        numbers: List = []
        try:
            numbers.append(data['international_phone_number'].replace(' ', ''))
            apofiz_add_organization['numbers'] = numbers
        except:
            apofiz_add_organization['numbers'] = []

        try:
            apofiz_add_organization['opens_at'] = data['current_opening_hours']['periods'][0]['open']['time'][:-2] \
                                                  + ':' + data['current_opening_hours']['periods'][0]['open']['time'][
                                                          2:]


            apofiz_add_organization['closes_at'] = data['current_opening_hours']['periods'][0]['close']['time'][:-2] \
                                                   + ':' + data['current_opening_hours']['periods'][0]['close']['time'][
                                                           2:]
        except:
            apofiz_add_organization['opens_at'] = None
            apofiz_add_organization['closes_at'] = None
        apofiz_add_organization['address'] = data['formatted_address'].replace(' - ', '. ')
        apofiz_add_organization['longitude'] = data['geometry']['location']['lng']
        apofiz_add_organization['latitude'] = data['geometry']['location']['lat']
        apofiz_add_organization['currency'] = cls.get_curency_CODE(data['address_components'][-1]['short_name'], request)
        apofiz_add_organization['country'] = cls.get_country_CODE(data['address_components'][-1]['short_name'], request)

        city_name = re.search(r'"(locality|region)">(.*?)</span>', data['adr_address']).group(2)
        apofiz_add_organization[
            'check_city'] = f'{cls.get_city_ID(city_name, request)} | {city_name}'  # для проверки правильности нахождния города
        apofiz_add_organization['city'] = cls.get_city_ID(city_name, request)
        place_type = data['types'][0]
        apofiz_add_organization['types'] = cls.get_place_type_ID(place_type, request)

        accounts: List = []
        try:
            accounts.append(data['website'])
            apofiz_add_organization['accounts'] = accounts
        except:
            apofiz_add_organization['accounts'] = []

        apofiz_add_organization['instagram_integration'] = None
        apofiz_add_organization['cards'] = []

        return apofiz_add_organization
