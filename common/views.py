import requests
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from drf_multiple_model.views import ObjectMultipleModelAPIView
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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
    queryset = Country.objects.select_related('currency').all()
    pagination_class = None


class CountryCitySearchView(ObjectMultipleModelAPIView):
    permission_classes = (AllowAny,)
    pagination_class = MultipleModelLimitOffsetPagination

    def get_querylist(self):
        search_param = self.request.query_params.get('search')

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


class YoutubeEmbedView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        youtube_link = request.GET.get('url', None)
        if not youtube_link:
            return Response({'message': 'Please pass the full youtube link'}, status=status.HTTP_400_BAD_REQUEST)

        embed_url = f'https://www.youtube.com/oembed?format=json&url={youtube_link}'
        response = requests.get(embed_url)
        if response.status_code == 200:
            return Response(response.json())

        return Response('salam')
