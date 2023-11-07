import requests
import base64
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from drf_multiple_model.views import ObjectMultipleModelAPIView
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException
from instagram_parsers.services.proxy_services import ProxyService
from mailer.services import MailerService
from organizations.services.organization_services import OrganizationService
from .constants import SHADOW_BAN
from .models import File, Country, Languages, FileVideo
from .serializers import ImageSerializer, CountrySerializer, CitySerializer, ImageFromUrlSerializer, \
    VersionSerializer, LanguagesListSerializer, ShadowBanSerializer, CurrencyConversionSerializer, \
    VideoFromUrlSerializer, LinkAppSerializer
from .services.country_city import CountryCityService
from .services.currency import CurrencyConverterService
from .services.others import LinkAppService
from .services.shadow import ShadowService
from .services.version import VersionService


class CurrencyConversion(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = CurrencyConversionSerializer(data=self.request.query_params)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        from_currency = serializer.validated_data['from_currency']
        to_currency = serializer.validated_data['to_currency']
        amount = serializer.validated_data['amount']

        amount = CurrencyConverterService.convert(from_currency=from_currency, to_currency=to_currency, amount=amount)
        answer = dict(from_currency=from_currency, to_currency=to_currency, amount=amount)
        data = CurrencyConversionSerializer(answer).data
        return Response(data=data)


class ShadowBanStatus(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShadowBanSerializer
    message_type = SHADOW_BAN

    def get_object(self):
        org_status = ShadowService.get_status(pk=self.kwargs['pk'])
        message = ShadowService.get_message(self.message_type, org_status)
        return message


class SendEmailToApofiz(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        organization = OrganizationService.get(pk=pk)
        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise NotAcceptableException(_('No rights to edit organization'))

        apofiz_email = settings.EMAIL_HOST_USER
        MailerService.send_shadow_ban_email(email=apofiz_email, org_id=pk, send_time=timezone.now())

        organization.is_under_review = True
        organization.save(update_fields=('is_under_review',))

        return Response(data={
            'message': _('Successfully send email.')
        }, status=status.HTTP_200_OK)


class ImageCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    serializer_class = ImageSerializer
    queryset = File.objects.all()


class ImageCreateFromUrlView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ImageFromUrlSerializer
    queryset = File.objects.all()


class VideoCreateFromUrlView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = VideoFromUrlSerializer
    queryset = FileVideo.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        thumbnail = File.objects.create(image_url=serializer.validated_data['thumbnail_url'])
        file_video = FileVideo.objects.create(video_url=serializer.validated_data['video_url'],
                                              thumbnail=thumbnail)

        # data = self.serializer_class(file_video).data
        return Response(self.serializer_class(file_video).data, status=status.HTTP_201_CREATED)
        # return Response(data={'message': _('Successfully created')}, status=status.HTTP_201_CREATED)


class WatermarkImageCreateView(ImageCreateView):
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['is_watermarked'] = True
        serializer = self.get_serializer(data=data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
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
            return Response({'message': _('Please pass the full youtube link')}, status=status.HTTP_400_BAD_REQUEST)

        embed_url = f'https://www.youtube.com/oembed?format=json&url={youtube_link}'
        response = requests.get(embed_url)
        if response.status_code == 200:
            return Response(response.json())

        return Response({'message': _('Please provide valid youtube link')}, status=status.HTTP_400_BAD_REQUEST)


class GetLatestAppVersion(RetrieveAPIView):
    serializer_class = VersionSerializer

    def get_object(self):
        return VersionService.get(device=self.kwargs['device'])


class LanguagesList(ListAPIView):
    pagination_class = None
    serializer_class = LanguagesListSerializer
    queryset = Languages.objects.select_related('flag').all()


class LinkAppAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        link = LinkAppService.get_link_app()
        if link:
            data = LinkAppSerializer(link).data
            return Response(data=data)
        else:
            return Response(
                {
                    'name_link': link
                }
            )


class ImageToBase64View(APIView):

    def get(self, request):
        image_url = request.query_params.get('image_url')

        if not image_url:
            return Response({'message': 'Image URL not provided'}, status=400)
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        try:
            response = requests.get(image_url, proxies=proxy[0])
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            image_data = response.content

            base64_data = base64.b64encode(image_data)
            base64_string = base64_data.decode('utf-8')

            return Response({'base64_image': base64_string}, status=200)
        except requests.exceptions.RequestException as e:
            return Response({'message': str(e)}, status=400)


class FileToBase64View(APIView):

    def get(self, request):
        file_url = request.query_params.get('file_url')

        if not file_url:
            return Response({'message': 'File URL not provided'}, status=400)
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        try:
            response = requests.get(file_url, proxies=proxy[0])
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            image_data = response.content

            base64_data = base64.b64encode(image_data)
            base64_string = base64_data.decode('utf-8')

            return Response({'base64_image': base64_string}, status=200)
        except requests.exceptions.RequestException as e:
            return Response({'message': str(e)}, status=400)
