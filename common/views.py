import re
from django.shortcuts import render
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from drf_multiple_model.views import ObjectMultipleModelAPIView
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from organizations.services.organization_services import OrganizationService
from .models import File, Country
from .serializers import ImageSerializer, CountrySerializer, CitySerializer, ImageFromUrlSerializer
from .services.country_city import CountryCityService


class ImageCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    serializer_class = ImageSerializer
    queryset = File.objects.all()


class ImageCreateFromUrlView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ImageFromUrlSerializer
    queryset = File.objects.all()


class WatermarkImageCreateView(ImageCreateView):
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['is_watermarked'] = True
        serializer = self.get_serializer(data=data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CountriesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CountrySerializer
    queryset = Country.objects.all()
    pagination_class = None


class CountryCitySearchView(ObjectMultipleModelAPIView):
    permission_classes = (AllowAny,)
    pagination_class = MultipleModelLimitOffsetPagination

    def get_querylist(self):
        search_param = self.request.query_params.get('search', None)

        countries, cities = CountryCityService.get_countries_and_cities(keyword=search_param)

        query_list = (
            {
                'queryset': countries,
                'serializer_class': CountrySerializer,
                'label': 'countries'
            },
            {
                'queryset': cities,
                'serializer_class': CitySerializer,
                'label': 'cities'
            }
        )
        return query_list


def index(request):
    return render(request, 'dist/index.html', {})


def organization_detail_view(request, pk):
    organization = OrganizationService.get(pk=pk)
    description = organization.description
    # description = description.replace(r'\n', ' ').replace(r'\r', '')
    description1 = re.sub("\n|\r", " ", description)

    context = {
        'organization': organization,
        'description': description1
    }
    return render(request, 'dist/index.html', context)
