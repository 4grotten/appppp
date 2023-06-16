from bs4 import BeautifulSoup as BS
from typing import List, Dict
import sys, os, re, json
import requests
import googlemaps
from django.conf import settings
from urllib.parse import urljoin
from rest_framework.exceptions import ValidationError

HEADERS = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Accept-Language': 'ru,ru-RU;q=0.9,en;q=0.8,ru-RU;q=0.7'
}




class GoogleMapsService:
    @classmethod
    def get_api_key(cls, *args, **kwargs):
        api_key = settings.GOOGLE_MAP_API_KEY
        return api_key

    @classmethod
    def get_place_CID(cls, gMaps_URL) -> str:
        try:
            session = requests.Session()
            response = session.get(gMaps_URL)
            text = response.url
            print(text)
            pattern = r'(?::|tid=)(0x[a-z0-9]+)(?:!|&hl=|\?utm_source=)'
            match = re.search(pattern, text)
            print("MATCH:", match)
            if match:
                print("IN MATCCH")
                cid_hexadecimal = match.group(1)
                print("cid_hexadecimal:", cid_hexadecimal)
                cid = str(int(cid_hexadecimal, 16))
                print("cid", cid)
                return cid
            else:
                print("ELSE STATEMEENT")
                error_data = {
                    "message": "Invalid input",
                    "errors": {
                        "google_maps_url": [
                            "Enter a valid URL."
                        ]
                    }
                }
                raise ValidationError(error_data)
        except:
            print("EXCEPT STATE")
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
    def get_place_details(cls, gMaps_URL: str) -> Dict:
        api_key = cls.get_api_key()

        cid = cls.get_place_CID(gMaps_URL)
        print("GOT CID:", cid)
        lang = '&language=ru'  # язык в котором будет json
        details_url = f'https://maps.googleapis.com/maps/api/place/details/json?cid={cid}&key={api_key}{lang}'
        print("details_url", details_url)
        r = requests.get(details_url)
        print("RESPONSE OF DETAILED_URL", r)
        place_details = r.json()
        print("PLACE_DETAILS", place_details)
        return place_details['result']

    @classmethod
    def get_image_ID(cls, gMaps_URL: str, request):
        json_data = {}
        r = requests.get(gMaps_URL)
        html = BS(r.text, 'lxml')
        place_image = html.select('meta[property="og:image"]')[0]['content']

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
        try:
            HEADERS = {'Authorization': token, 'Accept-Language': 'ru'}
            r_image = requests.post(url=URL_IMAGE_ENDPOINT, headers=HEADERS, data=query)
            json_data = json.loads(r_image.text)
            image_ID = json_data['id']

            return image_ID
        except:
            return json_data['detail']

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
        r = requests.get(URL_COUNTRIES_AND_CITIES)
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
        r = requests.get(URL_COUNTRIES_AND_CITIES)
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
        r = requests.get(URL_COUNTRIES_AND_CITIES)
        results = r.json().get('results', {})

        cities = results.get('cities', [])
        if cities:
            city_id = cities[0]['id']
            return city_id
        else:
            return None

    @classmethod
    def get_place_type_ID(cls, gMaps_URL, request):
        page_source = requests.get(gMaps_URL, headers=HEADERS).text

        match = re.search(r'(★|☆) · (.*?)" itemprop="description">', page_source)
        if match is None:
            return None

        place_type = match.group(2)
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
        r = requests.get(URL_ORGANIZATION_TYPES, headers=_headers)
        if r.json() == []:
            return None
            # return place_type
        else:
            for item in r.json():
                if item['title'] == place_type:
                    organization_type_ID = item['id']
                    return organization_type_ID
    @classmethod
    def add_organization(cls, gMaps_URL: str, request):
        data = cls.get_place_details(gMaps_URL)
        print("GOT PLACE DETAILS", data)

        apofiz_add_organization = {}

        apofiz_add_organization['title'] = data['name']
        print("GOT TITLE", apofiz_add_organization['title'])

        image_id = cls.get_image_ID(gMaps_URL, request)
        print("GOT IMAGE_ID", image_id)
        if image_id == 'Учетные данные не были предоставлены.':
            apofiz_add_organization[
                'image_id'] = 57323  # default geocode result icon из гугл карт на случай ошибки с картинкой
        else:
            apofiz_add_organization['image_id'] = image_id
        print("THE ACTUAL IMAGE:", apofiz_add_organization['image_id'])
        try:
            apofiz_add_organization['description'] = data['editorial_summary']['overview']
        except:
            apofiz_add_organization['description'] = ''
        print("GOT DESC",apofiz_add_organization['description'])

        numbers: List = []
        try:
            numbers.append(data['international_phone_number'].replace(' ', ''))
            apofiz_add_organization['numbers'] = numbers
        except:
            apofiz_add_organization['numbers'] = []
        print("GOT NUMBERS", apofiz_add_organization['numbers'])

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
        print("GOT OPENS AT:", apofiz_add_organization['opens_at'])
        print("GOT CLOSES AT:", apofiz_add_organization['closes_at'])
        apofiz_add_organization['address'] = data['formatted_address'].replace(' - ', '. ')
        print("GOT ADDRESS:", apofiz_add_organization['address'])
        apofiz_add_organization['longitude'] = data['geometry']['location']['lng']
        print("GOT LONGITUDE:", apofiz_add_organization['longitude'])
        apofiz_add_organization['latitude'] = data['geometry']['location']['lat']
        print("GOT LATITUDE:", apofiz_add_organization['latitude'])
        apofiz_add_organization['currency'] = cls.get_curency_CODE(data['address_components'][-1]['short_name'], request)
        print("GOT CURRENCY:", apofiz_add_organization['currency'])
        apofiz_add_organization['country'] = cls.get_country_CODE(data['address_components'][-1]['short_name'], request)
        print("GOT COUNTRY:", apofiz_add_organization['country'])

        city_name = re.search(r'"(locality|region)">(.*?)</span>', data['adr_address']).group(2)
        print("GOT CITY_NAME:", city_name)
        apofiz_add_organization[
            'check_city'] = f'{cls.get_city_ID(city_name, request)} | {city_name}'  # для проверки правильности нахождния города
        print("CHECKED_CITY:", apofiz_add_organization['check_city'])
        apofiz_add_organization['city'] = cls.get_city_ID(city_name, request)
        print("ACTUAL CITY:", apofiz_add_organization['city'])

        apofiz_add_organization['types'] = cls.get_place_type_ID(gMaps_URL, request)
        print("GOT TYPES:", apofiz_add_organization['types'])

        accounts: List = []
        try:
            accounts.append(data['website'])
            apofiz_add_organization['accounts'] = accounts
        except:
            apofiz_add_organization['accounts'] = []
        print("GOT ACCOUNTS:", apofiz_add_organization['accounts'])

        apofiz_add_organization['instagram_integration'] = None
        apofiz_add_organization['cards'] = []
        print("GOT CARDS:", apofiz_add_organization['cards'])
        print("FINISHED PARSING")
        return apofiz_add_organization
