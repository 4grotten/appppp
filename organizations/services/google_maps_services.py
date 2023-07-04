import sys, re, json
import requests

from django.conf import settings
from urllib.parse import urljoin
from typing import List, Dict
from rest_framework.exceptions import ValidationError
from instagram_parsers.services.proxy_services import ProxyService

COOKIES = {
    '_2gis_webapi_user': '9d9e9ba1-5aaf-40a3-846e-438a8bb1033a',
    '_ym_uid': '1638952700395286379',
    'ipp_uid': '1646311517080%2fhfGopZHXwiC266DR%2fhjmNPYIoz6HNKdxytE9gow%3d%3d',
    'ipp_uid1': '',
    'ipp_uid2': '',
    'ipp_uid_tst': '',
    'ipp_static_key': '',
    'dg5_jur': '{%22ru_sng%22:{%22status%22:%22agree%22%2C%22ts%22:1656398590507%2C%22v%22:2}}',
    'spid': '1661511089287_6bdc58bd69f3b0932c23875bf29fe1f5_ruxbx26r0hxfkt29',
    '_ym_d': '1673239575',
    'tmr_lvid': 'd3040bcc13db5b5dae1ca6e3c3c95ea5',
    'tmr_lvidTS': '1680520665191',
    '_2gis_webapi_session': '23b99453-e636-4ac1-9c5b-c53f906bbbb3',
    '_gid': 'GA1.2.167659839.1687409387',
    '_ym_isad': '2',
    'dg5_pos': '74.606476%3B42.88036%3B11.75',
    'spsc': '1687423830114_870bc4aaaf55dd8a56681b2a750b43e2_a5476469b72f558bb72e6aae99c6a060',
    '_ga': 'GA1.2.1479943786.1638952700',
    'tmr_detect': '0%7C1687423844441',
    '_gat_online5': '1',
    '_ga_LCKYJS0XZC': 'GS1.1.1687423615.8.1.1687423900.0.0.0',
}

HEADERS = {
    'authority': '2gis.kg',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}


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

            return json_data
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
                return country

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
            city_id = cities[0]
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
        type_list = []
        if r.json() == []:
            return None
        else:
            for item in r.json():
                if item['title'] == place_type:
                    type_list.append(item)
                    return type_list
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
            apofiz_add_organization['image'] = image_id
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
        apofiz_add_organization['full_location'] = {
            'latitude': data['geometry']['location']['lat'],
            'longitude': data['geometry']['location']['lng']
        }
        apofiz_add_organization['currency'] = cls.get_curency_CODE(data['address_components'][-1]['short_name'], request)
        apofiz_add_organization['country'] = cls.get_country_CODE(data['address_components'][-1]['short_name'], request)

        city_name = re.search(r'"(locality|region)">(.*?)</span>', data['adr_address']).group(2)
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


class TwoGisService:

    @classmethod
    def find_dict_in_json(cls, data, dict_name, path=""):
        if isinstance(data, dict):
            if dict_name in data:
                return data[dict_name]
            else:
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        result = cls.find_dict_in_json(value, dict_name, "{}['{}']".format(path, key))
                        if result is not None:
                            return result
        elif isinstance(data, list):
            for i in range(len(data)):
                if isinstance(data[i], (dict, list)):
                    result = cls.find_dict_in_json(data[i], dict_name, '{}[{}]'.format(path, i))
                    if result is not None:
                        return result
        return None

    @classmethod
    def place_images(cls, place_ID):
        base_url = 'https://api.photo.2gis.com/2.0/photo/get?'
        params = f'key=gYu1s9N1wP&' \
                 f'object_id={place_ID}&' \
                 'object_type=branch&' \
                 'locale=ru_KG&' \
                 'status=active&' \
                 'sort_by=position&' \
                 'album_code=common&' \
                 'preview_size=656x340&' \
                 'size=1&' \
                 'page=1'
        r = requests.get(base_url, params)

        for item in r.json()['result'][0]['items']:
            if item['is_pinned'] == True:
                if item['pinned_position'] == 1:
                    return item['url']
            else:
                return item['url']
            break

    @classmethod
    def get_image_ID(cls, image_URL, request):
        token = request.headers.get('Authorization')

        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_IMAGE_ENDPOINT = urljoin(base_url, 'save_image_from_url/')

        query = {
            'image_url': image_URL,
            'is_watermarked': True
        }
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        try:
            _headers = {'Authorization': token, 'Accept-Language': 'ru'}
            r = requests.post(url=URL_IMAGE_ENDPOINT, headers=_headers, data=query, proxies=proxy[0])

            json_data = json.loads(r.text)
            return json_data
        except Exception as e:
            return 59503

    @classmethod
    def get_place_type_ID(cls,place_type, request):
        token = request.headers.get('Authorization')

        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_PLACE_TYPE = urljoin(base_url, f'organization_all_types/?search={place_type}')

        _headers = {'Authorization': token, 'Accept-Language': 'ru'}

        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_PLACE_TYPE, headers=_headers, proxies=proxy[0])
        type_list = []
        try:
            if r.json() == []:
                return None
            else:
                for item in r.json():
                    if item['title'] == place_type.capitalize():
                        type_list.append(item)
                        return type_list
        except Exception as e:
            return None

    @classmethod
    def get_city_ID(cls, sity_name, request):
        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_CITY_ID = urljoin(base_url, f'countries_and_cities/?search={sity_name}')

        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_CITY_ID, proxies=proxy[0])
        city = r.json()['results']['cities'][0]

        return city

    @classmethod
    def get_country_CODE(cls,gMaps_country_short_name, request):
        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_COUNTRY_CODE = urljoin(base_url, f'countries_and_cities/?limit=240')

        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_COUNTRY_CODE, proxies=proxy[0])
        for country in r.json()['results']['countries']:
            if country['code'] == gMaps_country_short_name:
                return country

    @classmethod
    def get_curency_CODE(cls, gMaps_country_short_name, request):
        base_url = 'https://test.apofiz.com/api/v1/'  # Default base URL for dev version

        if 'localhost' in request.META['HTTP_HOST']:
            base_url = 'http://localhost:8000/api/v1/'  # Base URL for local development
        elif 'test.apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://test.apofiz.com/api/v1/'  # Base URL for dev version
        elif 'apofiz.com' in request.META['HTTP_HOST']:
            base_url = 'https://apofiz.com/api/v1/'  # Base URL for production version

        URL_CURRENCY_CODE = urljoin(base_url, f'countries_and_cities/?limit=240')

        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        r = requests.get(URL_CURRENCY_CODE, proxies=proxy[0])
        for country in r.json()['results']['countries']:
            if country['code'] == gMaps_country_short_name:
                return country['currency']['code']

    @classmethod
    def get_2gis_place_details(cls,URL_2gis: str) -> Dict:
        try:
            r = requests.get(URL_2gis, headers=HEADERS, cookies=COOKIES)
            result = re.search(r"var initialState = JSON.parse\('(.*?)'\);", r.text).group(1).replace('\\\\', '\\')
            place_details = json.loads(result)

            return place_details['data']
        except Exception as e:
            error_data = {
                "message": "Invalid input",
                "errors": {
                    "two_gis_url": [
                        "Enter a valid URL."
                    ]
                }
            }
            raise ValidationError(error_data)

    @classmethod
    def add_organization(cls, URL_2gis, request) -> Dict:
        data = cls.get_2gis_place_details(URL_2gis)

        apofiz_add_organization = {}

        place_ID = list(data['entity']['profile'].keys())[0]

        try:
            apofiz_add_organization['title'] = data["entity"]["profile"][place_ID]["data"]["name_ex"]["primary"]
        except Exception as e:
            apofiz_add_organization['title'] = ''

        try:
            place_logo = data['searchContext'][f'DEFAULT_SEARCH_ID_{place_ID}']['ads']['options']['logo'][
                'img_url'].strip("image.png")
            rect_logo_URL = f'{place_logo}image_512x512.png?api-version=2.0'
            if rect_logo_URL:
                apofiz_add_organization['image'] = cls.get_image_ID(rect_logo_URL, request)
        except Exception as e:
            apofiz_add_organization['image'] = cls.get_image_ID(cls.place_images(place_ID), request)

        try:
            seoStore = data['seoStore']['data']['description']
            try:
                searchContext = data['searchContext'][f'DEFAULT_SEARCH_ID_{place_ID}']['ads']['article'].replace(
                    '<br />', '\n')
                apofiz_add_organization['description'] = f'{searchContext}\n\n{seoStore}'
            except Exception as e:
                apofiz_add_organization['description'] = seoStore

        except Exception as e:
            apofiz_add_organization['description'] = ''

        numbers: List = []
        try:
            numbers.append(data['entity']['profile'][place_ID]['data']['contact_groups'][0]['contacts'][0]['value'])
            apofiz_add_organization['numbers'] = numbers
        except Exception as e:
            apofiz_add_organization['numbers'] = []

        try:
            opens_at = data['entity']['profile'][place_ID]['data']['schedule']['Mon']['working_hours'][0]['from']
            closes_at = data['entity']['profile'][place_ID]['data']['schedule']['Mon']['working_hours'][0]['to']

            if opens_at == "24:00":
                opens_at = "00:00"

            if closes_at == "24:00":
                closes_at = "00:00"

            apofiz_add_organization['opens_at'] = opens_at
            apofiz_add_organization['closes_at'] = closes_at
        except Exception as e:
            apofiz_add_organization['opens_at'] = None
            apofiz_add_organization['closes_at'] = None

        try:
            street_name = data['entity']['profile'][place_ID]['data']['address']['components'][0]['street']
            buinding_number = data['entity']['profile'][place_ID]['data']['address']['components'][0]['number']
            postcode = data['entity']['profile'][place_ID]['data']['address']['postcode']
            country = data['entity']['profile'][place_ID]['data']['adm_div'][0]['name']
            sity = data['entity']['profile'][place_ID]['data']['adm_div'][1]['name']
            district = data['entity']['profile'][place_ID]['data']['adm_div'][3]['name']
            try:
                address_comment = f"({data['entity']['profile'][place_ID]['data']['address_comment']})"
            except:
                address_comment = ''

            address = f'ул. {street_name}, д. {buinding_number} {address_comment} • {country} - {sity} - {district} ({postcode})'
            apofiz_add_organization['address'] = address
        except Exception as e:
            apofiz_add_organization['address'] = ''

        try:
            apofiz_add_organization['full_location'] = {
                'latitude': data['entity']['profile'][place_ID]['data']['point']['lat'],
                'longitude': data['entity']['profile'][place_ID]['data']['point']['lon']
            }
        except Exception as e:
            apofiz_add_organization['longitude'] = None
            apofiz_add_organization['latitude'] = None

        try:
            apofiz_add_organization['currency'] = cls.get_curency_CODE(
                data['region']['detector']['default']['data']['countryCode'].upper(), request)
        except Exception as e:
            apofiz_add_organization['currency'] = None

        try:
            apofiz_add_organization['country'] = cls.get_country_CODE(data['region']['detector']['default']['data']['countryCode'].upper(), request)
        except Exception as e:
            apofiz_add_organization['country'] = None

        try:
            apofiz_add_organization['city'] = cls.get_city_ID(data['region']['detector']['default']['data']['name'], request)
        except Exception as e:
            apofiz_add_organization['city'] = None

        try:
            apofiz_add_organization['types'] = cls.get_place_type_ID(
                data['entity']['profile'][place_ID]['data']['name_ex']['extension'], request)
        except:
            apofiz_add_organization['types'] = None

        accounts: List = []
        try:
            for link in data['entity']['profile'][place_ID]['data']['contact_groups'][0]['contacts']:
                if link.get('url') != None:
                    accounts.append(link['url'])
            accounts.append(URL_2gis)
            apofiz_add_organization['accounts'] = accounts
        except:
            apofiz_add_organization['accounts'] = []

        apofiz_add_organization['instagram_integration'] = None
        apofiz_add_organization['cards'] = []


        return apofiz_add_organization
