from typing import Union, Tuple

from django.db.models import QuerySet, Q

from common.models import City, Country


class CountryCityService:
    @classmethod
    def get_countries_and_cities(cls, keyword: Union[str, None]) -> Tuple[QuerySet, QuerySet]:
        country_filters = Q()
        city_filters = Q()

        if keyword:
            country_filters = (
                Q(name_en__istartswith=keyword) |
                Q(name_ru__istartswith=keyword) |
                Q(name_tr__istartswith=keyword)
            )
            city_filters = (
                Q(name_en__istartswith=keyword) |
                Q(name_ru__istartswith=keyword) |
                Q(name_tr__istartswith=keyword)
            )

        countries = Country.objects.filter(country_filters)
        cities = City.objects.filter(city_filters)

        return countries, cities
