import requests
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
from mailer.services import MailerService
from organizations.services.organization_services import OrganizationService
from .models import File, Country, Languages
from .serializers import ImageSerializer, CountrySerializer, CitySerializer, ImageFromUrlSerializer, \
    VersionSerializer, LanguagesListSerializer, ShadowBanSerializer
from .services.country_city import CountryCityService
from .services.shadow import ShadowService
from .services.version import VersionService


class ShadowBanStatus(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShadowBanSerializer
    message_type = 'shadow_ban'

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
