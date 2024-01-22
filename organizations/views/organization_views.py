import datetime
import random
import requests
import traceback
import json

from django.conf import settings
from django.utils.translation import activate
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, IntegerField, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView, ListAPIView, RetrieveAPIView, GenericAPIView, UpdateAPIView, CreateAPIView, DestroyAPIView,
    RetrieveUpdateAPIView
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, ObjectNotFoundException, IntegrityException
from common.models import File, Currency, Country, City
from common.utils import method_permission_classes
from common.services import slack
from mailer.services import MailerService
from organizations.constants import UNDER_REVIEW
from organizations.models import Organization, OrganizationCategory, OrganizationType, InstagramIntegration, Service, \
    OrganizationComplaint, OrganizationBlacklist, BlockedUser
from organizations.permissions import IsAnyOrganizationOwnerOrAdmin
from organizations.serializers.categories_serializers import (
    OrganizationCategorySerializer, HomepageOrganizationsSerializer, OrganizationWithDiscountsSerializer,
    OrganizationTypeSerializer
)
from organizations.serializers.misc_serializers import LocationSerializer
from organizations.serializers.organization_serializers import (
    OrganizationListSerializer, OrganizationCreateSerializer, OrganizationDetailedSerializer,
    OrganizationUpdateSerializer, OrgPhoneNumberSerializer, OrgPhoneNumberEditSerializer,
    OrgSocialNetworkContactSerializer, OrgSocialNetworkEditSerializer, OrganizationSerializer, OrgMessageSerializer,
    OrgMessageCreateSerializer, SubscriptionsMessageSerializer, OrganizationWithImageSerializer,
    InstagramIntegrationCreateUpdateSerializer, InstagramIntegrationLinkSerializer, DeliverySettingsUpdateSerializer,
    OrganizationTitleSerializer, OrgVerificationsSerializer, OrganizationComplaintSerializer,
    OrganizationBlacklistSerializer, BlockedUserSerializer, OrganizationGoogleMapsCreateSerializer,
    OrganizationTwoGisCreateSerializer, PaymentSystemSerializer, OrgPaymentSystemConfirmationSerializer,
    OrganizationMapsListSerializer
)
from organizations.serializers.query_param_serializers import (
    PartnerQueryParamSerializer, OrganizationAndCategorySerializer, OrganizationCoutrySerializer,
    OrganizationMapsLocationSerializer
)
from organizations.serializers.service_serializers import OrganizationServiceSerializer
from organizations.services.categories_services import OrganizationCategoryService
from organizations.services.google_maps_services import GoogleMapsService, TwoGisService
from organizations.services.organization_services import (
    OrganizationService, OrgPhoneNumberService, OrgSocialNetworkContactService, OrgMessageService,
    OrganizationInstagramIntegrationService
)
from organizations.services.subscription_services import SubscriptionService
from organizations.services.verifications_service import VerificationService, PaymentSystemConfirmationService
from organizations.tasks import (
    parse_instagram_to_shop_items, add_subscribers_to_organization
)
from shop.services.comment_services import CommentService
from users.serializers import UserShortInfoSerializer, FollowerOrClientSerializer


class OrgVerifications(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrgVerificationsSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        serializer = OrgVerificationsSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        VerificationService.create(organization, **serializer.validated_data)

        apofiz_email = settings.EMAIL_HOST_USER
        MailerService.send_verifications_email(email=apofiz_email, org_id=organization.pk, send_time=timezone.now())

        organization.verification_status = UNDER_REVIEW
        organization.save(update_fields=('verification_status',))

        return Response({"message": "verifications data successfully created"}, status=status.HTTP_201_CREATED)


class OrgPaymentSystemConfirmation(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrgPaymentSystemConfirmationSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        serializer = OrgPaymentSystemConfirmationSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        payment_system_id = serializer.validated_data.get('payment_system_id', None)
        if payment_system_id == 1:
            payment_system_name = "FreedomPay"
        elif payment_system_id == 2:
            payment_system_name = "PaySy"
        elif payment_system_id == 3:
            payment_system_name = "Crypto Box"
        else:
            raise NotAcceptableException(_('Unknown Payment System'))

        PaymentSystemConfirmationService.create(organization, **serializer.validated_data)

        apofiz_email = settings.EMAIL_HOST_USER
        MailerService.send_payment_verification_email(email=apofiz_email, org_id=organization.pk,
                                                      send_time=timezone.now(), payment_system_name=payment_system_name)

        return Response({"message": "Payment system data successfully created"}, status=status.HTTP_201_CREATED)


class OrgWholesaleConfirmation(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        if not organization.can_update_is_wholesale:
            apofiz_email = settings.EMAIL_HOST_USER
            MailerService.send_wholesale_verification_email(email=apofiz_email, org_id=organization.pk,
                                                            send_time=timezone.now())
            slack_message = (
                f'Organization\n'
                f'https://apofiz.com/971585333939admin/organizations/organization/{organization.pk}/change/\n'
                f'sent a connection request to the wholesale organization.\n'
                f'============================'
            )
            slack.bot(slack_message)
            organization.is_wholesale_request_timestamp = timezone.now()
            organization.save()

            return Response({"message": "Request successfully sent"}, status=status.HTTP_200_OK)

        return Response({"message": "You can already update the is_wholesale field"}, status=status.HTTP_200_OK)


class OrganizationCreationLimitView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = {
            'can_add_organization': not OrganizationService.creation_limit_exceeded(user=request.user),
            'is_delivery_service': OrganizationService.is_delivery_service(user=request.user)
        }
        return Response(data=data)


class OrganizationsListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(Q(owner=user) | Q(memberships__user=user)).annotate(
            priority=Case(When(owner=user, then=0), default=1, output_field=IntegerField(), )
        ).order_by('priority').distinct()

    def create(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.create_organization(**serializer.validated_data)

        num_members = random.randint(28, 130)
        if organization.country.code == 'AE':
            transaction.on_commit(lambda: add_subscribers_to_organization.delay(organization.id, num_members))

        data = OrganizationDetailedSerializer(organization, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class MyOrganizationsWithCanEditListCreateView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(Q(owner=user, is_deleted=False) |
                                           Q(memberships__user=user, is_deleted=False,
                                             memberships__role__can_edit_organization=True))


class OrganizationsMapsListView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationMapsListSerializer

    def get(self, request, *args, **kwargs):
        serializer = OrganizationMapsLocationSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        data = OrganizationService.get_organizations_by_location_for_map(type=serializer.validated_data['type'])

        return Response(data)


class OrganizationsMapsCountryCityListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationMapsListSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title']

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        country = serializer.validated_data['country']
        city = serializer.validated_data['city']
        type = serializer.validated_data['type']

        return OrganizationService.get_organizations_by_country_city_for_map(country=country, city=city, type=type)


class OrganizationsGoogleMapsCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationGoogleMapsCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        google_maps_url = serializer.validated_data['google_maps_url']
        parsed_data = GoogleMapsService.add_organization(google_maps_url, request)
        return Response(parsed_data)


class OrganizationsTwoGisCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationTwoGisCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        two_gis_url = serializer.validated_data['two_gis_url']
        parsed_data = TwoGisService.add_organization(two_gis_url, request)
        return Response(parsed_data)


class OrganizationTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = OrganizationCategorySerializer
    queryset = OrganizationCategory.objects.all()


class OrganizationAllTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = OrganizationTypeSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ['category']
    search_fields = ['title']
    queryset = OrganizationType.objects.all()


class OrganizationMapsTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationTypeSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ['category']
    search_fields = ['title']

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        return OrganizationService.get_organization_types_by_country(country=serializer.validated_data['country'])


class OrganizationRetrieveUpdateView(RetrieveAPIView):
    serializer_class = OrganizationDetailedSerializer
    queryset = Organization.objects.all()

    def get_queryset(self):
        queryset = OrganizationService.get_working_time_status(self.queryset, self.request)
        return queryset

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if (datetime.datetime.now() - instance.add_item_date.replace(
                tzinfo=None)).days > 6 and instance.owner == self.request.user:
            OrganizationService.update_add_item_date(instance=instance, user=request.user)
            serializer = self.serializer_class(instance, context={'need_add_item': True, 'request': request})
            return Response(serializer.data)
        serializer = self.serializer_class(instance, context={'request': request})
        return Response(serializer.data)

    @method_permission_classes((IsAuthenticated,))
    def put(self, request, *args, **kwargs):
        serializer = OrganizationUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        updated_organization = OrganizationService.update(organization=organization, **serializer.validated_data)
        return Response(self.serializer_class(updated_organization, context={'request': request}).data)


class OrganizationPaymentSystemsActivationView(RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        organization = self.get_object()
        payment_systems_activated = organization.payment_systems_activated
        payment_with_confirmation = organization.payment_with_confirmation
        return Response({"payment_systems_activated": payment_systems_activated,
                         "payment_with_confirmation": payment_with_confirmation},
                        status=status.HTTP_200_OK)

    def get_object(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=self.request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        return organization

    def update(self, request, *args, **kwargs):
        organization = self.get_object()
        payment_systems_activated = request.data.get('payment_systems_activated', None)
        payment_with_confirmation = request.data.get('payment_with_confirmation', None)

        if payment_systems_activated is not None:
            organization.payment_systems_activated = payment_systems_activated
            organization.save()

        if payment_with_confirmation is not None:
            organization.payment_with_confirmation = payment_with_confirmation
            organization.save()

        return Response({"message": _("Payment systems settings updated.")},
                        status=status.HTTP_200_OK)


class OrganizationPaymentSystemsActivationDetailView(RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=self.request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        return organization

    def update(self, request, *args, **kwargs):
        organization = self.get_object()

        id = request.data.get('id', None)
        is_active = request.data.get('is_active', None)

        if id == 1:
            organization.freedompay_activated = is_active
            organization.save()
        elif id == 2:
            organization.paysy_activated = is_active
            organization.save()
        else:
            raise NotAcceptableException(_('Unknown Payment System'))


        return Response({"message": _("Activation status successfully updated.")},
                        status=status.HTTP_200_OK)


class DeliverySettingsView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeliverySettingsUpdateSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data)

    def get_object(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=self.request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        return organization

    def put(self, request, *args, **kwargs):
        try:
            return super().put(request, *args, **kwargs)
        except ValidationError as error:
            return Response(
                data={
                    'message': _('Invalid input'),
                    'errors': error.detail
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )


class DeactivateOrganizationView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        deactivated_organization = OrganizationService.deactivate(organization=organization)

        return Response(self.serializer_class(deactivated_organization, context={'request': request}).data)


class ReactivateOrganizationView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        deactivated_organization = OrganizationService.reactivate(organization=organization)

        return Response(self.serializer_class(deactivated_organization, context={'request': request}).data)


class ResetPurchaseIDView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        OrganizationService.reset_running_purchase_id(organization=organization)
        return Response(data={'message': _('Successfully reset running purchase ID')}, status=status.HTTP_200_OK)


class OrgPhonesListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        numbers = OrgPhoneNumberService.get_numbers_of_organization(organization_id=kwargs['pk'])
        data = OrgPhoneNumberSerializer(numbers, many=True).data
        return Response(data)

    def post(self, request, **kwargs):
        serializer = OrgPhoneNumberEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        numbers = OrgPhoneNumberService.update_phone_numbers(
            organization_id=kwargs['pk'], user=request.user, numbers=serializer.validated_data['phone_numbers'])
        data = OrgPhoneNumberSerializer(numbers, many=True).data
        return Response(data={
            'message': _('Successfully updated'),
            'numbers': data
        }, status=status.HTTP_200_OK)


class OrgNetworksListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        networks = OrgSocialNetworkContactService.get_networks_of_organization(organization_id=kwargs['pk'])
        data = OrgSocialNetworkContactSerializer(networks, many=True).data
        return Response(data)

    def post(self, request, **kwargs):
        serializer = OrgSocialNetworkEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        networks = OrgSocialNetworkContactService.update_social_networks(
            organization_id=kwargs['pk'], user=request.user, urls=serializer.validated_data['networks'])
        data = OrgSocialNetworkContactSerializer(networks, many=True).data
        return Response(data={
            'message': _('Successfully updated'),
            'networks': data
        }, status=status.HTTP_200_OK)


class SetOrganizationLocationAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = LocationSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=pk)

        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise NotAcceptableException(_('No rights to edit organization'))

        changed_organization = OrganizationService.set_location(
            organization=organization,
            longitude=serializer.validated_data.get('longitude'),
            latitude=serializer.validated_data.get('latitude'),
            address=serializer.validated_data.get('address')
        )

        data = OrganizationSerializer(changed_organization, context={'request': request}).data

        return Response(data={
            'message': _('Successfully updated'),
            'data': data
        }, status=status.HTTP_200_OK)


class HomepageOrganizationsView(ListAPIView):
    serializer_class = HomepageOrganizationsSerializer
    partner = None
    country = None
    city = None

    def get_queryset(self):
        serializer = PartnerQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid partner id, country and city are required in query parameters'))
        self.partner = serializer.validated_data['partner']
        self.city = serializer.validated_data['city']
        if self.city is None:
            self.country = serializer.validated_data['country']

        return OrganizationCategoryService.get_nonempty_categories(partner=self.partner, country=self.country,
                                                                   city=self.city)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['partner'] = self.partner
        context['country'] = self.country
        context['city'] = self.city
        context['request'] = self.request
        return context


class OrganizationsInCategoryView(ListAPIView):
    filter_backends = (SearchFilter,)
    search_fields = ('title',)
    serializer_class = OrganizationWithDiscountsSerializer

    def get_queryset(self):
        serializer = OrganizationAndCategorySerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _('Valid category, partner id, country and city are required in query parameters'))

        category = serializer.validated_data['category']
        partner = serializer.validated_data['partner']
        country = serializer.validated_data['country']
        city = serializer.validated_data['city']

        queryset = OrganizationService.get_organizations_in_category(category=category, partner=partner,
                                                                     country=country, city=city)
        return queryset


class OrganizationsInServicesView(ListAPIView):
    serializer_class = OrganizationServiceSerializer
    queryset = Organization.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['title']

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _('Valid country, city  are required in query parameters'))

        country = serializer.validated_data['country']
        city = serializer.validated_data['city']
        subcategory = serializer.validated_data['subcategory']
        try:
            service = Service.objects.get(id=self.kwargs['pk'])
        except ObjectDoesNotExist:
            raise ObjectNotFoundException
        queryset = OrganizationService.get_organizations_in_service(service=service,
                                                                    country=country, city=city,
                                                                    subcategory=subcategory, request=self.request)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['name'] = Service.objects.filter(id=self.kwargs['pk']).values_list('name', flat=True).first()
        return response


class HomepageSearchView(ListAPIView):
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('title',)
    filterset_fields = ('country', 'city',)
    serializer_class = OrganizationWithDiscountsSerializer

    def get_queryset(self):
        serializer = PartnerQueryParamSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)

        partner = serializer.validated_data['partner']
        if partner is None:
            return Organization.active_organizations.filter(is_active=True)

        return OrganizationService.get_organization_partners(organization=partner)


class SubscriptionsMessageListAPIView(ListAPIView):
    serializer_class = SubscriptionsMessageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('organization',)

    def get_queryset(self):
        messages = OrgMessageService.get_messages_of_organization(organization_id=self.request.GET['organization'])
        return messages

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['wallpapers'] = CommentService.get_wallpapers()
        return response


class OrgMessageAPIView(ListAPIView):
    serializer_class = OrgMessageSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        messages = OrgMessageService.get_messages_of_organization(organization_id=self.kwargs['pk'])
        return messages

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['wallpapers'] = CommentService.get_wallpapers()
        return response

    def post(self, request, *args, **kwargs):
        serializer = OrgMessageCreateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=kwargs['pk'])

        if not OrganizationService.user_can_send_message(organization_id=kwargs['pk'], user=request.user):
            raise PermissionDenied({'message': _('No rights to send message to followers of this organization')})
        OrgMessageService.send_message(organization=organization, content=serializer.validated_data.get('content'),
                                       sender=request.user, message_to=serializer.validated_data.get('message_to'))
        return Response(data={'message': _('Message is created')},
                        status=status.HTTP_201_CREATED)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request

        return context


class OrganizationTitleRetrieveAPIView(RetrieveAPIView):
    serializer_class = OrganizationTitleSerializer
    queryset = OrganizationService.filter()

    def get_serializer_context(self):
        context = super(OrganizationTitleRetrieveAPIView, self).get_serializer_context()
        context['request'] = self.request

        return context


class InstagramAccountAPIView(APIView):
    def post(self, request):
        serializer = InstagramIntegrationCreateUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        data = OrganizationInstagramIntegrationService.check_instagram_account(url=serializer.validated_data.get('url'))
        return Response(data=dict(url=serializer.validated_data.get('url'), user_profile=data),
                        status=status.HTTP_200_OK)


class InstagramParseLastDataAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})
        if not InstagramIntegration.objects.get(organization=organization):
            raise ObjectNotFoundException(_('Instagram Integration Link not found'))
        transaction.on_commit(
            lambda: parse_instagram_to_shop_items.delay(organization_id=organization.id, posts_count=20, anonymous=True)
        )
        return Response({'message': _('Success')})


class InstagramIntegrationCreateRetrieveAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})
        data = OrganizationInstagramIntegrationService.get_from_org(organization=organization)
        return Response(
            InstagramIntegrationLinkSerializer(data, context={'request': request}).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = InstagramIntegrationCreateUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=kwargs['pk'])

        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})
        instance = OrganizationInstagramIntegrationService.create(organization=organization,
                                                                  url=serializer.validated_data.get('url'))
        data = InstagramIntegrationLinkSerializer(instance, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})
        OrganizationInstagramIntegrationService.delete(organization=organization)
        return Response({'message': _('Successfully deleted')})


class OrganizationFollowersCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        users = SubscriptionService.get_organization_followers(organization_id=pk)[:3]
        count = SubscriptionService.get_organization_followers(organization_id=pk).count()

        return Response(data={
            'followers': UserShortInfoSerializer(users, many=True, context={'request': request}).data,
            'count': count
        }, status=status.HTTP_200_OK)


class OrganizationPartnersCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        organization = OrganizationService.get(id=pk)
        count, partners = OrganizationService.get_partners_dict(organization=organization)

        return Response(data={
            'partners': OrganizationWithImageSerializer(partners, many=True, context={'request': request}).data,
            'count': count,
        }, status=status.HTTP_200_OK)


class OrganizationPartnersFollowersCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        users = SubscriptionService.get_organization_partners_followers(organization_id=pk)[:3]
        count = SubscriptionService.get_organization_partners_followers(organization_id=pk).count()

        return Response(data={
            'followers': UserShortInfoSerializer(users, many=True, context={'request': request}).data,
            'count': count
        }, status=status.HTTP_200_OK)


class OrganizationClientDetailsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        user = OrganizationService.get_online_client(organization_id=kwargs['organization_id'],
                                                     requested_by=self.request.user, user_id=kwargs['user_id'])
        data = FollowerOrClientSerializer(
            user,
            context={'request': request, 'organization_id': kwargs['organization_id']}
        ).data
        return Response(data, status=status.HTTP_200_OK)


class OrganizationComplaintCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = OrganizationComplaint.objects.all()
    serializer_class = OrganizationComplaintSerializer

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except IntegrityError:
            raise IntegrityException(_('You have already complained about this item'))


class OrganizationBlackListCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = OrganizationBlacklist.objects.all()
    serializer_class = OrganizationBlacklistSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)

class OrganizationBlackListDestroyView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        try:
            blacklist = OrganizationBlacklist.objects.get(user=self.request.user, organization_id=self.kwargs['pk']).delete()
            return Response(data={
                'message': _('Successfully deleted'),
            }, status=status.HTTP_200_OK)
        except OrganizationBlacklist.DoesNotExist:
            raise ObjectNotFoundException(_('OrganizationBlacklist not found'))


class BlockUserCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, IsAnyOrganizationOwnerOrAdmin)
    serializer_class = BlockedUserSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)

class UnblockUserDestroyView(DestroyAPIView):
    permission_classes = (IsAuthenticated, IsAnyOrganizationOwnerOrAdmin)

    def destroy(self, request, *args, **kwargs):
        try:
            blocked_user = BlockedUser.objects.get(user_id=self.kwargs['user_id'], organization_id=self.kwargs['organization_id']).delete()
            return Response(data={
                'message': _('Successfully unblocked'),
            }, status=status.HTTP_200_OK)
        except BlockedUser.DoesNotExist:
            raise ObjectNotFoundException(_('BlockedUser not found'))


class OrganizationPaymentSystemListView(generics.ListAPIView):
    serializer_class = PaymentSystemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        organization_id = self.kwargs.get('pk')

        organization = OrganizationService.get(id=organization_id)

        if not OrganizationService.user_can_edit_organization(user=self.request.user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))

        confirmed_payment_systems = []
        if organization.freedompay_confirmed:
            confirmed_payment_systems.append({'id': 1, 'name': 'FreedomPay оплата в KGS',
                                              'is_active': organization.freedompay_activated})
        if organization.paysy_confirmed:
            confirmed_payment_systems.append({'id': 2, 'name': 'PaySy в USD',
                                              'is_active': organization.paysy_activated})

        return confirmed_payment_systems


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PaymentSystemListView(generics.ListAPIView):
    serializer_class = PaymentSystemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        organization_id = self.request.query_params.get('organization_id', None)
        if organization_id is None:
            return []

        organization = OrganizationService.get(pk=organization_id)
        available_payment_systems = []
        if not organization.freedompay_confirmed:
            available_payment_systems.append({'id': 1, 'name': 'FreedomPay оплата в KGS', 'is_available': True})
        if not organization.paysy_confirmed:
            available_payment_systems.append({'id': 2, 'name': 'PaySy в TRC', 'is_available': False})

        return available_payment_systems


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TranslateNamesOfOrgCategory(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        name_translations = {
            'Горнодобывающая промышленность': {'tr': 'Madencilik Endüstrisi', 'de': 'Bergbauindustrie', 'zh': '采矿工业'},
            'Спорт и спортивное питание': {'tr': 'Spor ve Sporcu Beslenmesi', 'de': 'Sport und Sporternährung',
                                           'zh': '体育和运动营养'},
            'Гостиницы, Отели, Туризм, Отдых': {'tr': 'Otel, Tatil, Turizm', 'de': 'Hotels, Tourismus, Erholung',
                                                'zh': '酒店，旅馆，旅游，休闲'},
            'Телекоммуникации и Связь': {'tr': 'Telekomünikasyon ve İletişim', 'de': 'Telekommunikation und Verbindung',
                                         'zh': '电信和通信'},
            'Сельское, водное, лесное хозяйство': {'tr': 'Kırsal, Su, Orman İşletmeciliği',
                                                   'de': 'Landwirtschaft, Wasser, Forstwirtschaft', 'zh': '农业，水域，林业'},
            'Недвижимость': {'tr': 'Emlak', 'de': 'Immobilien', 'zh': '房地产'},
            'Легкая и Текстильная промышленность': {'tr': 'Hafif ve Tekstil Endüstrisi',
                                                    'de': 'Leicht- und Textilindustrie', 'zh': '轻工和纺织工业'},
            'Юридические услуги': {'tr': 'Hukuki Hizmetler', 'de': 'Rechtsdienstleistungen', 'zh': '法律服务'},
            'Пищевая и продуктовая промышленность': {'tr': 'Gıda ve Gıda Endüstrisi',
                                                     'de': 'Lebensmittel- und Getränkeindustrie', 'zh': '食品和饮料工业'},
            'Авиа и ЖД Перевозки': {'tr': 'Havayolu ve Demiryolu Taşımacılığı', 'de': 'Luft- und Schienenverkehr',
                                    'zh': '航空和铁路运输'},
            'Еда, Клубы, Кино': {'tr': 'Yemek, Kulüpler, Sinema', 'de': 'Essen, Clubs, Kino', 'zh': '美食，俱乐部，电影'},
            'Услуги и сервисы': {'tr': 'Hizmetler ve Servisler', 'de': 'Dienstleistungen und Services', 'zh': '服务和服务'},
            'Отдых и развлечения': {'tr': 'Eğlence ve Eğlence', 'de': 'Freizeit und Unterhaltung', 'zh': '休闲和娱乐'},
            'Здоровье и Медицина': {'tr': 'Sağlık ve Tıp', 'de': 'Gesundheit und Medizin', 'zh': '健康和医学'},
            'Магазины и торговля': {'tr': 'Mağazalar ve Ticaret', 'de': 'Geschäfte und Handel', 'zh': '商店和贸易'},
            'Обслуживание предприятий': {'tr': 'İşletme Hizmetleri', 'de': 'Unternehmensdienstleistungen',
                                         'zh': '企业服务'},
            'Строительство': {'tr': 'İnşaat', 'de': 'Bauwesen', 'zh': '建筑'},
            'Электроэнергетика': {'tr': 'Elektrik Enerjisi', 'de': 'Elektrizitätswirtschaft', 'zh': '电力工业'},
            'Мебель': {'tr': 'Mobilya', 'de': 'Möbel', 'zh': '家具'},
            'Бизнес и финансы': {'tr': 'İş ve Finans', 'de': 'Business und Finanzen', 'zh': '商业和金融'},
            'Наука и Образование': {'tr': 'Bilim ve Eğitim', 'de': 'Wissenschaft und Bildung', 'zh': '科学和教育'},
            'Общественные организации': {'tr': 'Sivil Toplum Kuruluşları', 'de': 'Gemeinnützige Organisationen',
                                         'zh': '公益组织'},
            'Металлообрабатывающая промышленность': {'tr': 'Metal İşleme Endüstrisi',
                                                     'de': 'Metallverarbeitende Industrie', 'zh': '金属加工工业'},
            'СМИ, Полиграфия и Реклама': {'tr': 'Medya, Matbaacılık ve Reklam', 'de': 'Medien, Druck und Werbung',
                                          'zh': '传媒，印刷和广告'},
            'IT-Сфера и услуги': {'tr': 'IT Sektörü ve Hizmetleri', 'de': 'IT-Branche und Dienstleistungen',
                                  'zh': 'IT行业和服务'},
            'Торговые центры, рынки, базары': {'tr': 'Alışveriş Merkezleri, Pazarlar', 'de': 'Einkaufszentren, Märkte',
                                               'zh': '购物中心，市场'},
            'Красота': {'tr': 'Güzellik', 'de': 'Schönheit', 'zh': '美容'},
            'Инвестиции': {'tr': 'Yatırımlar', 'de': 'Investitionen', 'zh': '投资'},
            'Авто и транспорт': {'tr': 'Otomotiv ve Ulaşım', 'de': 'Auto und Verkehr', 'zh': '汽车和交通'},
            'Химическая промышленность': {'tr': 'Kimya Endüstrisi', 'de': 'Chemieindustrie', 'zh': '化学工业'}
        }

        for original_name, translations in name_translations.items():
            try:
                items = OrganizationCategory.objects.filter(name_ru=original_name)

                for item in items:
                    activate('tr')
                    item.name = translations.get('tr', original_name)
                    item.save()

                    activate('de')
                    item.name = translations.get('de', original_name)
                    item.save()

                    activate('zh')
                    item.name = translations.get('zh', original_name)
                    item.save()

                    activate('en')

            except OrganizationCategory.DoesNotExist:
                print(f"OrganizationCategory with name '{original_name}' does not exist.")
                continue

        return Response(data={'message': _('Translations added successfully')}, status=status.HTTP_200_OK)


class TranslateNamesOfOrgType(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        name_translations = {
            'Компания альтернативных источников энергии': {'tr': 'Alternatif Enerji Şirketi',
                                                           'de': 'Unternehmen für alternative Energiequellen',
                                                           'zh': '替代能源公司'},
            'Суши ресторан': {'tr': 'Sushi Restoranı', 'de': 'Sushi Restaurant', 'zh': '寿司餐厅'},
            'Ландшафтные дизайн услуги': {'tr': 'Peyzaj Tasarım Hizmetleri', 'de': 'Landschaftsdesign-Dienstleistungen',
                                          'zh': '景观设计服务'},
            'Гипермаркет': {'tr': 'Hipermarket', 'de': 'Hypermarkt', 'zh': '超级市场'},
            'Заливка фундамента': {'tr': 'Temel Dökme', 'de': 'Fundamentfüllung', 'zh': '基础灌浆'},
            'Авиа экспресс доставка': {'tr': 'Hava Ekspres Teslimat', 'de': 'Luftexpresslieferung', 'zh': '航空快递服务'},
            'Ремонт бытовой техники': {'tr': 'Ev Aletleri Onarımı', 'de': 'Haushaltsgeräte-Reparatur', 'zh': '家电维修'},
            'Охранная компания': {'tr': 'Güvenlik Şirketi', 'de': 'Sicherheitsunternehmen', 'zh': '保安公司'},
            'Сахарный производитель': {'tr': 'Şeker Üreticisi', 'de': 'Zuckerhersteller', 'zh': '糖生产商'},
            'Высшее учебное заведение (ВУЗ)': {'tr': 'Yükseköğretim Kurumu (YÜZ)', 'de': 'Hochschuleinrichtung',
                                               'zh': '高等教育机构'},
            'Хлопководство и переработка хлопка': {'tr': 'Pamuk Üretimi ve İşleme',
                                                   'de': 'Baumwollanbau und -verarbeitung', 'zh': '棉花种植和加工'},
            'Научное учреждение': {'tr': 'Bilimsel Kuruluş', 'de': 'Wissenschaftliche Einrichtung', 'zh': '科研机构'},
            'Охотничий магазин': {'tr': 'Avcılık Mağazası', 'de': 'Jagdgeschäft', 'zh': '狩猎用品店'},
            'Торговый Центр': {'tr': 'Alışveriş Merkezi', 'de': 'Einkaufszentrum', 'zh': '购物中心'},
            'Вино-водочный магазин': {'tr': 'Şarap ve Votka Mağazası', 'de': 'Wein- und Spirituosenladen',
                                      'zh': '葡萄酒和伏特加商店'},
            'Авто маляр': {'tr': 'Oto Boyacı', 'de': 'Autolackierer', 'zh': '汽车喷漆'},
            'Кулинарный цех': {'tr': 'Mutfak Atölyesi', 'de': 'Küchenwerkstatt', 'zh': '烹饪车间'},
            'Модельное агентство': {'tr': 'Model Ajansı', 'de': 'Modelagentur', 'zh': '模特经纪公司'},
            'Салон одежды': {'tr': 'Kuaför', 'de': 'Kleidungssalon', 'zh': '服装沙龙'},
            'Строительство заборов': {'tr': 'Çit İnşaatı', 'de': 'Zaunbau', 'zh': '篱笆建造'},
            'Народное образование': {'tr': 'Halk Eğitimi', 'de': 'Volksbildung', 'zh': '民间教育'},
            'Нотариальная контора': {'tr': 'Noter Bürosu', 'de': 'Notarbüro', 'zh': '公证处'},
            'Метало корпусные конструкции': {'tr': 'Metal Gövde Yapıları', 'de': 'Metallgehäusekonstruktionen',
                                             'zh': '金属外壳结构'},
            'Табачный склад': {'tr': 'Tütün Deposu', 'de': 'Tabaklager', 'zh': '烟草仓库'},
            'Магазин обоев': {'tr': 'Duvar Kağıdı Mağazası', 'de': 'Tapetenladen', 'zh': '墙纸商店'},
            'Экспертная медкомиссия': {'tr': 'Uzman Tıbbi Komisyon', 'de': 'Fachärztliche Kommission', 'zh': '专业医学委员会'},
            'Магазин спорт товаров': {'tr': 'Spor Malzemeleri Mağazası', 'de': 'Sportartikelladen', 'zh': '体育用品商店'},
            'Магазин сумок': {'tr': 'Çanta Mağazası', 'de': 'Taschengeschäft', 'zh': '手袋商店'},
            'Автомойка': {'tr': 'Oto Yıkama', 'de': 'Autowaschanlage', 'zh': '汽车洗车站'},
            'Трансмиссионные работы': {'tr': 'Aktarım Onarımları', 'de': 'Getriebereparaturen', 'zh': '传动系统维修'},
            'Частный собственник': {'tr': 'Özel Sahip', 'de': 'Privatbesitzer', 'zh': '私人业主'},
            'Магазин сувениров и подарков': {'tr': 'Hediyelik Eşya ve Hediye Mağazası',
                                             'de': 'Souvenir- und Geschenkeladen', 'zh': '纪念品和礼品商店'},
            'Мебель производство': {'tr': 'Mobilya Üretimi', 'de': 'Möbelherstellung', 'zh': '家具制造'},
            'Ремонт двигателя': {'tr': 'Motor Onarımı', 'de': 'Motorenreparatur', 'zh': '发动机维修'},
            'Агентство оценки': {'tr': 'Değerleme Ajansı', 'de': 'Bewertungsagentur', 'zh': '评估机构'},
            'Кинотеатр': {'tr': 'Sinema', 'de': 'Kino', 'zh': '电影院'},
            'Стоматологические центр': {'tr': 'Diş Hekimliği Merkezi', 'de': 'Zahnmedizinisches Zentrum', 'zh': '牙科中心'},
            'Боулинг Центр': {'tr': 'Bowling Merkezi', 'de': 'Bowlingzentrum', 'zh': '保龄球中心'},
            'Продукция пчеловодства': {'tr': 'Arıcılık Ürünleri', 'de': 'Imkereiprodukte', 'zh': '养蜂产品'},
            'Лесное угодье': {'tr': 'Orman Alanı', 'de': 'Waldgebiet', 'zh': '森林地带'},
            'Канцелярский магазин': {'tr': 'Kırtasiye Mağazası', 'de': 'Büromaterialgeschäft', 'zh': '文具商店'},
            'Ночной клуб': {'tr': 'Gece Kulübü', 'de': 'Nachtclub', 'zh': '夜总会'},
            'Создание сайтов': {'tr': 'Web Sitesi Oluşturma', 'de': 'Webseitenerstellung', 'zh': '网站制作'},
            'Компания ремонта и отделки': {'tr': 'Onarım ve Dekorasyon Şirketi',
                                           'de': 'Renovierungs- und Dekorationsunternehmen', 'zh': '装修公司'},
            'Неправительственная организация (НПО)': {'tr': 'Sivil Toplum Kuruluşu (STK)',
                                                      'de': 'Nichtregierungsorganisation (NGO)', 'zh': '非政府组织 (NGO)'},
            'Парк аттракционов': {'tr': 'Eğlence Parkı', 'de': 'Freizeitpark', 'zh': '游乐园'},
            'Овощной склад': {'tr': 'Sebze Deposu', 'de': 'Gemüselager', 'zh': '蔬菜仓库'},
            'Скалодром': {'tr': 'Tırmanma Duvarı', 'de': 'Kletterwand', 'zh': '攀岩墙'},
            'Магазин детской одежды': {'tr': 'Çocuk Giyim Mağazası', 'de': 'Kinderbekleidungsgeschäft', 'zh': '儿童服装店'},
            'Колбасная фабрика': {'tr': 'Sosis Fabrikası', 'de': 'Wurstfabrik', 'zh': '香肠工厂'},
            'Цветочный магазин': {'tr': 'Çiçekçi', 'de': 'Blumengeschäft', 'zh': '花店'},
            'Дошкольные центр': {'tr': 'Okul Öncesi Merkezi', 'de': 'Kindergarten', 'zh': '幼儿园中心'},
            'Профессиональный лицей': {'tr': 'Meslek Lisesi', 'de': 'Berufsschule', 'zh': '职业高中'},
            'Государственный нотариус': {'tr': 'Devlet Noteri', 'de': 'Staatsnotar', 'zh': '国家公证处'},
            'Малярная камера': {'tr': 'Boyahane', 'de': 'Lackierkabine', 'zh': '喷漆室'},
            'Джинсовый магазин': {'tr': 'Jeans Mağazası', 'de': 'Jeansladen', 'zh': '牛仔店'},
            'Архитектурно проектная компания': {'tr': 'Mimarlık ve Proje Şirketi',
                                                'de': 'Architektur- und Planungsfirma', 'zh': '建筑和规划公司'},
            'Банкетный зал': {'tr': 'Banket Salonu', 'de': 'Bankettsaal', 'zh': '宴会厅'},
            'Лакокрасочный цех': {'tr': 'Boya ve Vernik Atölyesi', 'de': 'Lackierwerkstatt', 'zh': '油漆和清漆车间'},
            'Производитель чипсов': {'tr': 'Cips Üreticisi', 'de': 'Chiphersteller', 'zh': '薯片生产商'},
            'Оздоровительный комплексы': {'tr': 'Sağlık ve İyileştirme Kompleksi', 'de': 'Erholungskomplex',
                                          'zh': '康复中心'},
            'Угольная компания добыча и производство': {'tr': 'Kömür Şirketi Madencilik ve Üretim',
                                                        'de': 'Kohleunternehmen Bergbau und Produktion',
                                                        'zh': '煤炭公司采矿和生产'},
            'Аптека': {'tr': 'Eczane', 'de': 'Apotheke', 'zh': '药店'},
            'Ветеринарная служба': {'tr': 'Veteriner Hizmet', 'de': 'Tierärztlicher Dienst', 'zh': '兽医服务'},
            'Клининговая компания': {'tr': 'Temizlik Şirketi', 'de': 'Reinigungsunternehmen', 'zh': '清洁公司'},
            'Центр экспертизы': {'tr': 'Uzmanlık Merkezi', 'de': 'Expertisezentrum', 'zh': '鉴定中心'},
            'Оптика центр': {'tr': 'Optik Merkez', 'de': 'Optik Zentrum', 'zh': '光学中心'},
            'Аудио, фото, видеотехника магазин': {'tr': 'Ses, Fotoğraf, Video Teknik Mağaza',
                                                  'de': 'Audio, Foto, Video Technik Geschäft', 'zh': '音频、照片、视频技术商店'},
            'Магазин обуви': {'tr': 'Ayakkabı Mağazası', 'de': 'Schuhgeschäft', 'zh': '鞋店'},
            'Электроэнергетика': {'tr': 'Elektrik Enerjisi', 'de': 'Elektroenergie', 'zh': '电力工程'},
            'Ресторан': {'tr': 'Restoran', 'de': 'Restaurant', 'zh': '餐厅'},
            'Оптика магазин': {'tr': 'Optik Mağaza', 'de': 'Optik Geschäft', 'zh': '光学商店'},
            'Цирюльня': {'tr': 'Terzi Dükkanı', 'de': 'Schneiderei', 'zh': '裁缝店'},
            'Музыкальная школа': {'tr': 'Müzik Okulu', 'de': 'Musikschule', 'zh': '音乐学校'},
            'Производитель теплоизоляционных материалов': {'tr': 'Yalıtım Malzemeleri Üreticisi',
                                                           'de': 'Hersteller von Wärmedämmmaterialien',
                                                           'zh': '隔热材料制造商'},
            'Торговые дом': {'tr': 'Ticaret Evi', 'de': 'Handelshaus', 'zh': '商业公司'},
            'Бытовая техника и электроника магазин': {'tr': 'Ev Aletleri ve Elektronik Mağaza',
                                                      'de': 'Haushaltsgeräte und Elektronik Geschäft',
                                                      'zh': '家用电器和电子产品商店'},
            'Строительство подстанций': {'tr': 'Alt İstasyon İnşaatı', 'de': 'Unterstationsbau', 'zh': '变电站建设'},
            'Мясомолочная фабрика': {'tr': 'Et ve Süt Fabrikası', 'de': 'Fleisch- und Molkereifabrik', 'zh': '肉奶工厂'},
            'Пластическая хирургия': {'tr': 'Plastik Cerrahi', 'de': 'Plastische Chirurgie', 'zh': '整形外科'},
            'Компания телекоммуникаций': {'tr': 'Telekomünikasyon Şirketi', 'de': 'Telekommunikationsunternehmen',
                                          'zh': '电信公司'},
            'Гараж': {'tr': 'Garaj', 'de': 'Garage', 'zh': '车库'},
            'Медицинская лаборатория': {'tr': 'Tıbbi Laboratuvar', 'de': 'Medizinisches Labor', 'zh': '医学实验室'},
            'Сырный цех': {'tr': 'Peynir Fabrikası', 'de': 'Käserei', 'zh': '奶酪车间'},
            'Промышленное оборудование': {'tr': 'Endüstriyel Ekipman', 'de': 'Industrieausrüstung', 'zh': '工业设备'},
            'Кулинария': {'tr': 'Mutfak Sanatları', 'de': 'Kochkunst', 'zh': '烹饪'},
            'Другие виды авто услуг': {'tr': 'Diğer Araç Hizmetleri', 'de': 'Andere Arten von Auto-Dienstleistungen',
                                       'zh': '其他汽车服务'},
            'Производитель сырных изделий': {'tr': 'Peynir Ürünleri Üreticisi', 'de': 'Hersteller von Käseprodukten',
                                             'zh': '奶酪制品制造商'},
            'Птицефабрика': {'tr': 'Tavuk Fabrikası', 'de': 'Geflügelfabrik', 'zh': '禽类工厂'},
            'Логистическая компания': {'tr': 'Lojistik Şirketi', 'de': 'Logistikunternehmen', 'zh': '物流公司'},
            'Угольная компания': {'tr': 'Kömür Şirketi', 'de': 'Kohleunternehmen', 'zh': '煤炭公司'},
            'Автоцентр': {'tr': 'Oto Merkezi', 'de': 'Autozentrum', 'zh': '汽车中心'},
            'Метало база': {'tr': 'Metal Deposu', 'de': 'Metallbasis', 'zh': '金属基地'},
            'Эмитентны виртуальных активов': {'tr': 'Sanal Varlık Yayıncısı',
                                              'de': 'Emittent von virtuellen Vermögenswerten', 'zh': '虚拟资产发行者'},
            'Галерея': {'tr': 'Galeri', 'de': 'Galerie', 'zh': '画廊'},
            'Компания производитель защиты растений': {'tr': 'Bitki Koruma Ürünleri Üreticisi',
                                                       'de': 'Hersteller von Pflanzenschutzmitteln', 'zh': '植物保护制品制造商'},
            'Машинист': {'tr': 'Makinist', 'de': 'Maschinist', 'zh': '机械师'},
            'Земельно-строительная компания': {'tr': 'İnşaat ve Arazi Şirketi', 'de': 'Bau- und Grundstücksunternehmen',
                                               'zh': '土地建设公司'},
            'Магазин сантехника': {'tr': 'Tesisat Malzemeleri Mağazası', 'de': 'Sanitärtechnik Geschäft', 'zh': '卫浴店'},
            'Продюсерский центр': {'tr': 'Prodüksiyon Merkezi', 'de': 'Produktionszentrum', 'zh': '制片中心'},
            'Ремонт электро отопительных котлов': {'tr': 'Elektrikli Isıtma Kazanları Onarımı',
                                                   'de': 'Reparatur von elektrischen Heizkesseln', 'zh': '电暖锅炉维修'},
            'Товары для животных': {'tr': 'Hayvan Ürünleri', 'de': 'Tierprodukte', 'zh': '宠物用品'},
            'Первичное жилье': {'tr': 'Birincil Konut', 'de': 'Erstwohnung', 'zh': '首次购房'},
            'Сварка': {'tr': 'Kaynak', 'de': 'Schweißen', 'zh': '焊接'},
            'Частная школа': {'tr': 'Özel Okul', 'de': 'Privatschule', 'zh': '私立学校'},
            'Детский дом': {'tr': 'Çocuk Yuvası', 'de': 'Kinderheim', 'zh': '儿童之家'},
            'Информационные технологии': {'tr': 'Bilgi Teknolojileri', 'de': 'Informationstechnologie', 'zh': '信息技术'},
            'Адвокатская контора': {'tr': 'Avukatlık Bürosu', 'de': 'Anwaltskanzlei', 'zh': '律师事务所'},
            'Замена авто зеркал': {'tr': 'Ayna Değişimi', 'de': 'Austausch der Autofenster', 'zh': '汽车镜替换'},
            'Комплекс отдыха': {'tr': 'Tatil Kompleksi', 'de': 'Erholungskomplex', 'zh': '度假村'},
            'Производитель интернет продуктов': {'tr': 'İnternet Ürünleri Üreticisi',
                                                 'de': 'Hersteller von Internetprodukten', 'zh': '互联网产品制造商'},
            'Частный наркологический центр': {'tr': 'Özel Narkoloji Merkezi', 'de': 'Privates Narkologiezentrum',
                                              'zh': '私人麻醉学中心'},
            'Торговый комплекс': {'tr': 'Alışveriş Kompleksi', 'de': 'Einkaufszentrum', 'zh': '购物中心'},
            'Пассажирские авиаперевозки': {'tr': 'Yolcu Havayolu Taşımacılığı', 'de': 'Passagierflugverkehr',
                                           'zh': '客运航空'},
            'Ювелирный холдинг': {'tr': 'Mücevher Holding', 'de': 'Schmuckunternehmen', 'zh': '珠宝控股'},
            'Продуктовая Палатка': {'tr': 'Gıda Çadırı', 'de': 'Lebensmittelzelt', 'zh': '食品帐篷'},
            'Косместолог': {'tr': 'Kozmetolog', 'de': 'Kosmetologe', 'zh': '美容学家'},
            'ЖД служба доставки': {'tr': 'Demiryolu Teslimat Hizmeti', 'de': 'Eisenbahn-Lieferdienst', 'zh': '铁路送货服务'},
            'Шашлычная': {'tr': 'Şiş Kebap Restoranı', 'de': 'Grillrestaurant', 'zh': '烤肉店'},
            'Анимационная студия': {'tr': 'Animasyon Stüdyosu', 'de': 'Animationsstudio', 'zh': '动画工作室'},
            'Детективные агентство': {'tr': 'Detektif Ajansı', 'de': 'Detektivagentur', 'zh': '侦探机构'},
            'Реабилитационный центр': {'tr': 'Rehabilitasyon Merkezi', 'de': 'Rehabilitationszentrum', 'zh': '康复中心'},
            'Таксопарк': {'tr': 'Taksi Parkı', 'de': 'Taxistand', 'zh': '出租车站'},
            'Овощная база': {'tr': 'Sebze Deposu', 'de': 'Gemüselager', 'zh': '蔬菜基地'},
            'Магазин продовольственных товаров': {'tr': 'Gıda Malzemeleri Mağazası', 'de': 'Lebensmittelgeschäft',
                                                  'zh': '食品杂货店'},
            'Хлебопродуктовый цех': {'tr': 'Ekmek ve Unlu Mamuller Atölyesi', 'de': 'Bäckerei', 'zh': '面包糕点车间'},
            'Санитарно-эпидемиологическая служба': {'tr': 'Sağlık ve Epidemiyoloji Servisi',
                                                    'de': 'Gesundheits- und Epidemiologiedienst', 'zh': '卫生与流行病学服务'},
            'Магазин купальников и аксессуаров': {'tr': 'Mayo ve Aksesuar Mağazası',
                                                  'de': 'Badebekleidungs- und Accessoire-Geschäft', 'zh': '比基尼和配饰店'},
            'Компьютерные курсы': {'tr': 'Bilgisayar Kursları', 'de': 'Computerkurse', 'zh': '计算机课程'},
            'Галерея Кафеля': {'tr': 'Seramik Galerisi', 'de': 'Fliesengalerie', 'zh': '瓷砖画廊'},
            'Компания грузоперевозки': {'tr': 'Nakliye Şirketi', 'de': 'Transportunternehmen', 'zh': '货运公司'},
            'Бильярдный зал': {'tr': 'Bilardo Salonu', 'de': 'Billardzimmer', 'zh': '台球室'},
            'Поставщик теплоизоляционных материалов': {'tr': 'Yalıtım Malzemeleri Tedarikçisi',
                                                       'de': 'Lieferant für Wärmedämmmaterialien', 'zh': '隔热材料供应商'},
            'Кейтеринг': {'tr': 'Catering', 'de': 'Catering', 'zh': '餐饮服务'},
            'Оптический центр': {'tr': 'Optik Merkezi', 'de': 'Optikzentrum', 'zh': '光学中心'},
            'Этнические объединение': {'tr': 'Etnik Birlik', 'de': 'Ethnische Vereinigung', 'zh': '民族团结'},
            'Веб студия': {'tr': 'Web Stüdyosu', 'de': 'Webstudio', 'zh': '网络工作室'},
            'Брокерская компания': {'tr': 'Broker Şirketi', 'de': 'Brokerfirma', 'zh': '经纪公司'},
            'Информационное агентство': {'tr': 'Bilgi Ajansı', 'de': 'Informationsagentur', 'zh': '信息机构'},
            'Спортивный комплекс': {'tr': 'Spor Kompleksi', 'de': 'Sportkomplex', 'zh': '体育综合设施'},
            'Кафе': {'tr': 'Kafe', 'de': 'Café', 'zh': '咖啡馆'},
            'Рихтовальный цех': {'tr': 'Düzeltme Atölyesi', 'de': 'Richtwerkstatt', 'zh': '整形车间'},
            'Рознично торговая компания': {'tr': 'Perakende Ticaret Şirketi', 'de': 'Einzelhandelsunternehmen',
                                           'zh': '零售公司'},
            'Нотариус': {'tr': 'Noter', 'de': 'Notar', 'zh': '公证人'},
            'Производитель масло растительного': {'tr': 'Bitkisel Yağ Üreticisi', 'de': 'Pflanzenölhersteller',
                                                  'zh': '植物油生产商'},
            'Выделка кожсырья': {'tr': 'Deri İşleme Fabrikası', 'de': 'Lederbearbeitungsfabrik', 'zh': '皮革加工厂'},
            'Цирковая арена': {'tr': 'Sirk Arena', 'de': 'Zirkusarena', 'zh': '马戏场'},
            'Системы кондиционирования и вентиляции': {'tr': 'Havalandırma ve Klima Sistemleri',
                                                       'de': 'Klima- und Lüftungssysteme', 'zh': '空调和通风系统'},
            'Гражданское строительство': {'tr': 'Sivil İnşaat', 'de': 'Zivile Bauarbeiten', 'zh': '民用建筑'},
            'Производитель укупорочных изделий': {'tr': 'Kapak Üreticisi', 'de': 'Verschluss Hersteller',
                                                  'zh': '封口制品生产商'},
            'Ремонт и отделка': {'tr': 'Onarım ve Dekorasyon', 'de': 'Reparatur und Dekoration', 'zh': '修理和装饰'},
            'Инвестиционный компания': {'tr': 'Yatırım Şirketi', 'de': 'Investmentfirma', 'zh': '投资公司'},
            'Гипсобетонные изделия': {'tr': 'Alçı Beton Ürünleri', 'de': 'Gipsbetonprodukte', 'zh': '石膏混凝土制品'},
            'Скорая медицинская помощь': {'tr': 'Acil Tıbbi Yardım', 'de': 'Notfallmedizin', 'zh': '急救医疗服务'},
            'Строительная дизайн студия': {'tr': 'İnşaat Tasarım Stüdyosu', 'de': 'Bau-Design-Studio', 'zh': '建筑设计工作室'},
            'Барбер шоп': {'tr': 'Berber Dükkanı', 'de': 'Barbershop', 'zh': '理发店'},
            'Около таможенная инфраструктура': {'tr': 'Gümrük Yakını Altyapı', 'de': 'Naher Grenzübergang',
                                                'zh': '靠近海关的基础设施'},
            'Магазин мужской одежды': {'tr': 'Erkek Giyim Mağazası', 'de': 'Herrenbekleidungsgeschäft', 'zh': '男装店'},
            'Магазин натуральной косметики': {'tr': 'Doğal Kozmetik Mağazası', 'de': 'Naturkosmetikgeschäft',
                                              'zh': '天然化妆品店'},
            'Нефтяная компания': {'tr': 'Petrol Şirketi', 'de': 'Ölunternehmen', 'zh': '石油公司'},
            'Ломбард': {'tr': 'Lombard', 'de': 'Pfandhaus', 'zh': '当铺'},
            'Фармацевтические компания': {'tr': 'İlaç Şirketi', 'de': 'Pharmazeutisches Unternehmen', 'zh': '制药公司'},
            'Агентство доставки': {'tr': 'Teslimat Ajansı', 'de': 'Lieferagentur', 'zh': '快递代理'},
            'Типография': {'tr': 'Matbaa', 'de': 'Druckerei', 'zh': '印刷厂'},
            'Осветительная и светотехническая продукция': {'tr': 'Aydınlatma ve Işık Teknolojisi Ürünleri',
                                                           'de': 'Beleuchtungs- und Lichttechnikprodukte',
                                                           'zh': '照明和光技术产品'},
            'Техникум': {'tr': 'Teknik Okul', 'de': 'Technikum', 'zh': '技术学院'},
            'Магазин детских игрушек': {'tr': 'Çocuk Oyuncak Mağazası', 'de': 'Spielzeugladen für Kinder',
                                        'zh': '儿童玩具店'},
            'Центр акушерства и гинекологии': {'tr': 'Obstetrik ve Jinekoloji Merkezi',
                                               'de': 'Geburtshilfe und Gynäkologie Zentrum', 'zh': '产科和妇科中心'},
            'Пластиковое производство: тара, упаковка, пластиковая продукция': {
                'tr': 'Plastik Üretimi: Ambalaj, Paketleme, Plastik Ürünler',
                'de': 'Kunststoffproduktion: Verpackung, Verpackung, Kunststoffprodukte', 'zh': '塑料生产：包装，包装，塑料制品'},
            'Кузовные работы': {'tr': 'Gövde İşleri', 'de': 'Karosseriearbeiten', 'zh': '车身工作'},
            'Спортивно оздоровительный центр': {'tr': 'Spor ve Sağlık Merkezi', 'de': 'Sport- und Gesundheitszentrum',
                                                'zh': '运动与健康中心'},
            'Магазин нижнего белья': {'tr': 'Alt Giyim Mağazası', 'de': 'Unterwäsche-Geschäft', 'zh': '内衣店'},
            'Ювелирный бутик': {'tr': 'Mücevher Butik', 'de': 'Schmuckboutique', 'zh': '珠宝精品店'},
            'Противоугонные системы': {'tr': 'Hırsızlık Önleme Sistemleri', 'de': 'Diebstahlsicherungssysteme',
                                       'zh': '防盗系统'},
            'Фитнес центр': {'tr': 'Fitness Merkezi', 'de': 'Fitnesszentrum', 'zh': '健身中心'},
            'Текстиль': {'tr': 'Tekstil', 'de': 'Textil', 'zh': '纺织品'},
            'Переработка меха': {'tr': 'Kürk Geri Dönüşümü', 'de': 'Pelzverarbeitung', 'zh': '皮草加工'},
            'Конный центр': {'tr': 'At Merkezi', 'de': 'Pferdezentrum', 'zh': '马术中心'},
            'Профессиональное училище': {'tr': 'Mesleki Okul', 'de': 'Berufsschule', 'zh': '职业学校'},
            'Спортивный зал': {'tr': 'Spor Salonu', 'de': 'Sporthalle', 'zh': '体育馆'},
            'Магазин технических систем безопасности': {'tr': 'Güvenlik Sistemleri Mağazası',
                                                        'de': 'Geschäft für Sicherheitssysteme', 'zh': '安全系统商店'},
            'Столярные изделия': {'tr': 'Marangoz Ürünleri', 'de': 'Tischlerwaren', 'zh': '木工制品'},
            'Мясо перерабатывающий завод': {'tr': 'Et İşleme Fabrikası', 'de': 'Fleischverarbeitungswerk',
                                            'zh': '肉类加工厂'},
            'Производитель соли': {'tr': 'Tuz Üreticisi', 'de': 'Salzhersteller', 'zh': '盐生产商'},
            'Парк отдыха': {'tr': 'Eğlence Parkı', 'de': 'Freizeitpark', 'zh': '休闲公园'},
            'Кредитные компания': {'tr': 'Kredi Şirketi', 'de': 'Kreditgesellschaft', 'zh': '信贷公司'},
            'Фруктовая база': {'tr': 'Meyve Depo', 'de': 'Obstlager', 'zh': '水果基地'},
            'Страховая компания': {'tr': 'Sigorta Şirketi', 'de': 'Versicherungsgesellschaft', 'zh': '保险公司'},
            'Кулинарный магазин': {'tr': 'Mutfak Mağazası', 'de': 'Kochgeschäft', 'zh': '烹饪商店'},
            'Установка подстанции': {'tr': 'Alt İstasyon Kurulumu', 'de': 'Umspannwerksinstallation', 'zh': '变电站安装'},
            'Подбор персонала': {'tr': 'Personel Seçimi', 'de': 'Personalrekrutierung', 'zh': '人才招聘'},
            'Тату салон': {'tr': 'Dövme Salonu', 'de': 'Tattoo Salon', 'zh': '纹身沙龙'},
            'Мебельный магазин': {'tr': 'Mobilya Mağazası', 'de': 'Möbelgeschäft', 'zh': '家具商店'},
            'Эротический магазин': {'tr': 'Erotik Mağaza', 'de': 'Erotikgeschäft', 'zh': '色情商店'},
            'Горнодобывающая техника и оборудование': {'tr': 'Dağ Madenciliği Teknolojisi ve Ekipmanı',
                                                       'de': 'Bergbau- und Ausrüstungstechnik', 'zh': '采矿技术和设备'},
            'Дистрибьюторская компания': {'tr': 'Distribütör Şirketi', 'de': 'Verteilerunternehmen', 'zh': '经销公司'},
            'Компания кондиционирования и вентиляции': {'tr': 'Klima ve Havalandırma Şirketi',
                                                        'de': 'Klima- und Lüftungsunternehmen', 'zh': '空调和通风公司'},
            'Колбасный цех': {'tr': 'Sosis Üretim Atölyesi', 'de': 'Wurstwerkstatt', 'zh': '香肠厂'},
            'Стоянка': {'tr': 'Park Alanı', 'de': 'Parkplatz', 'zh': '停车场'},
            'Лаборатория': {'tr': 'Laboratuvar', 'de': 'Labor', 'zh': '实验室'},
            'Здоровое Кафе': {'tr': 'Sağlıklı Kafe', 'de': 'Gesundes Café', 'zh': '健康咖啡馆'},
            'Производитель упакованных орехов': {'tr': 'Ambalajlı Ceviz Üreticisi',
                                                 'de': 'Hersteller von verpackten Nüssen', 'zh': '包装坚果制造商'},
            'Финансовый брокер': {'tr': 'Finans Brokeri', 'de': 'Finanzmakler', 'zh': '金融经纪人'},
            'Сахарный завод': {'tr': 'Şeker Fabrikası', 'de': 'Zuckerfabrik', 'zh': '糖厂'},
            'Судебно-медицинская экспертиза': {'tr': 'Adli Tıp İncelemesi', 'de': 'Gerichtsmedizinische Untersuchung',
                                               'zh': '法医鉴定'},
            'Магазин спортивной одежды': {'tr': 'Spor Giyim Mağazası', 'de': 'Sportbekleidungsgeschäft', 'zh': '运动服装店'},
            'Ткани': {'tr': 'Kumaşlar', 'de': 'Stoffe', 'zh': '布料'},
            'Свадебный салон': {'tr': 'Düğün Salonu', 'de': 'Hochzeitssalon', 'zh': '婚纱店'},
            'Колбасный производитель': {'tr': 'Sosis Üreticisi', 'de': 'Wursthersteller', 'zh': '香肠制造商'},
            'Стриптиз бар': {'tr': 'Striptiz Bar', 'de': 'Stripclub', 'zh': '脱衣舞酒吧'},
            'Центры по проведению бизнес и информационных мероприятий': {'tr': 'İş ve Bilgi Etkinlikleri Merkezi',
                                                                         'de': 'Unternehmens- und Informationsveranstaltungszentren',
                                                                         'zh': '商务和信息活动中心'},
            'Все для дома': {'tr': 'Ev İçin Her Şey', 'de': 'Alles für das Zuhause', 'zh': '家居用品'},
            'Магазин морепродуктов': {'tr': 'Deniz Ürünleri Mağazası', 'de': 'Fischgeschäft', 'zh': '海鲜店'},
            'Магазин фототоваров': {'tr': 'Fotoğraf Malzemeleri Mağazası', 'de': 'Fotowarenladen', 'zh': '摄影器材店'},
            'Гипсокартонные конструкции': {'tr': 'Alçıpan Yapı', 'de': 'Gipskartonkonstruktionen', 'zh': '石膏板结构'},
            'Курьерская связь': {'tr': 'Kurye İletişimi', 'de': 'Kurierverbindung', 'zh': '快递服务'},
            'Мясомолочный комбинат': {'tr': 'Et ve Süt İşleme Tesisi', 'de': 'Fleisch- und Milchverarbeitungsanlage',
                                      'zh': '肉奶综合加工厂'},
            'Мебель мягкая': {'tr': 'Yumuşak Mobilya', 'de': 'Polstermöbel', 'zh': '软家具'},
            'Частная поликлиника': {'tr': 'Özel Poliklinik', 'de': 'Private Poliklinik', 'zh': '私人诊所'},
            'Хвойный питомник': {'tr': 'Çam Fidanlığı', 'de': 'Nadelbaum-Nursery', 'zh': '针叶苗圃'},
            'Ритуальные услуги': {'tr': 'Ritüel Hizmetleri', 'de': 'Bestattungsdienstleistungen', 'zh': '丧葬服务'},
            'Колледж': {'tr': 'Kolej', 'de': 'Hochschule', 'zh': '学院'},
            'Магазин строительной техники': {'tr': 'İnşaat Teknolojisi Mağazası', 'de': 'Baumarkt', 'zh': '建筑技术商店'},
            'Сельхоз объединения': {'tr': 'Tarım Birlikleri', 'de': 'Landwirtschaftliche Genossenschaften',
                                    'zh': '农业合作社'},
            'Рихтовщик': {'tr': 'Düzeltici', 'de': 'Richter', 'zh': '修车工'},
            'Текстильный магазин': {'tr': 'Tekstil Mağazası', 'de': 'Textilgeschäft', 'zh': '纺织品商店'},
            'Производитель Алкогольной продукции': {'tr': 'Alkol Üreticisi', 'de': 'Alkoholproduzent', 'zh': '酒类制品制造商'},
            'Гипсовые изделия': {'tr': 'Alçı Ürünleri', 'de': 'Gipsprodukte', 'zh': '石膏制品'},
            'Магазин строительно-отделочных материалов': {'tr': 'İnşaat ve Dekorasyon Malzemeleri Mağazası',
                                                          'de': 'Baustoff- und Ausstattungsgeschäft',
                                                          'zh': '建筑和装饰材料商店'},
            'Производитель пива': {'tr': 'Bira Üreticisi', 'de': 'Brauerei', 'zh': '啤酒制造商'},
            'Эвакуатор': {'tr': 'Çekici', 'de': 'Abschleppwagen', 'zh': '拖车'},
            'Работа с гипсокартонном': {'tr': 'Alçıpan İşleri', 'de': 'Gipskartonarbeit', 'zh': '石膏板工程'},
            'Ремонт Трансформаторов, подстанции': {'tr': 'Transformatör ve Alt İstasyon Onarımı',
                                                   'de': 'Transformator- und Umspannwerkreparatur', 'zh': '变压器和变电站维修'},
            'Мука молочный комбинат': {'tr': 'Un Süt Kombinası', 'de': 'Mehl-Molkerei-Kombination', 'zh': '面粉乳品联合企业'},
            'Охота': {'tr': 'Avcılık', 'de': 'Jagd', 'zh': '狩猎'},
            'Сеть быстрого питания': {'tr': 'Hızlı Yiyecek Zinciri', 'de': 'Fast-Food-Kette', 'zh': '快餐连锁'},
            'Образовательный комплекс': {'tr': 'Eğitim Kompleksi', 'de': 'Bildungskomplex', 'zh': '教育综合体'},
            'Ледовая арена': {'tr': 'Buz Arena', 'de': 'Eisarena', 'zh': '溜冰场'},
            'Религиозный университет': {'tr': 'Din Üniversitesi', 'de': 'Theologische Universität', 'zh': '宗教大学'},
            'СПА центр': {'tr': 'SPA Merkezi', 'de': 'Wellness-Zentrum', 'zh': '水疗中心'},
            'Децентрализованая биржа': {'tr': 'Merkezi Olmayan Borsa', 'de': 'Dezentralisierte Börse', 'zh': '去中心化交易所'},
            'Другие виды туризма': {'tr': 'Diğer Turizm Türleri', 'de': 'Andere Arten von Tourismus', 'zh': '其他旅游方式'},
            'Магазин женской одежды': {'tr': 'Kadın Giyim Mağazası', 'de': 'Damenbekleidungsgeschäft', 'zh': '女装店'},
            'СТО - Автосервис': {'tr': 'Oto Servis', 'de': 'Kfz-Werkstatt', 'zh': '汽车维修服务站'},
            'Центр по развитию сельского хозяйства': {'tr': 'Kırsal Kalkınma Merkezi',
                                                      'de': 'Zentrum für ländliche Entwicklung', 'zh': '农业发展中心'},
            'Автошкола': {'tr': 'Sürücü Kursu', 'de': 'Fahrschule', 'zh': '驾校'},
            'Теплоэнергетика': {'tr': 'Termal Enerji', 'de': 'Wärmeenergie', 'zh': '热能'},
            'Почтовая служба': {'tr': 'Posta Hizmeti', 'de': 'Postdienst', 'zh': '邮政服务'},
            'Радиостанция': {'tr': 'Radyo İstasyonu', 'de': 'Radiosender', 'zh': '无线电站'},
            'Компания лифтового оборудования и грузоподъемной техники': {
                'tr': 'Asansör ve Kaldırma Ekipmanları Şirketi', 'de': 'Aufzugs- und Fördertechnikunternehmen',
                'zh': '电梯和起重设备公司'},
            'Лакокрасочная компания': {'tr': 'Boya ve Vernik Şirketi', 'de': 'Farb- und Lackunternehmen', 'zh': '涂料公司'},
            'Некоммерческая организация (НКО)': {'tr': 'Kâr Amacı Gütmeyen Kuruluş (KAGK)',
                                                 'de': 'Non-Profit-Organisation (NPO)', 'zh': '非营利组织（NPO）'},
            'Производство пластмассы и пластмассовых изделий': {'tr': 'Plastik Üretimi ve Plastik Ürünleri',
                                                                'de': 'Kunststoffherstellung und Kunststoffprodukte',
                                                                'zh': '塑料制品生产和塑料制品'},
            'Геологическая разведка и изыскания': {'tr': 'Jeolojik Keşif ve Araştırma',
                                                   'de': 'Geologische Erkundung und Untersuchungen', 'zh': '地质勘探和矿产调查'},
            'Биржевой брокер': {'tr': 'Borsa Brokeri', 'de': 'Börsenmakler', 'zh': '交易所经纪人'},
            'Автошеринг': {'tr': 'Araç Paylaşım', 'de': 'Carsharing', 'zh': '共享汽车'},
            'Строительство и ремонт': {'tr': 'İnşaat ve Onarım', 'de': 'Bau und Reparatur', 'zh': '建筑和维修'},
            'Филармония': {'tr': 'Filarmoni', 'de': 'Philharmonie', 'zh': '交响乐团'},
            'Базар': {'tr': 'Pazar', 'de': 'Basar', 'zh': '市场'},
            'Молочная фабрика': {'tr': 'Süt Fabrikası', 'de': 'Milchfabrik', 'zh': '乳品工厂'},
            'Ремонт оборудования': {'tr': 'Ekipman Onarımı', 'de': 'Gerätereparatur', 'zh': '设备维修'},
            'Обменное бюро': {'tr': 'Döviz Bürosu', 'de': 'Wechselstube', 'zh': '货币兑换处'},
            'Правообладатель': {'tr': 'Hak Sahibi', 'de': 'Rechteinhaber', 'zh': '权利所有人'},
            'Дизайн студия': {'tr': 'Tasarım Stüdyosu', 'de': 'Designstudio', 'zh': '设计工作室'},
            'Спортивное питание': {'tr': 'Sporcu Beslenmesi', 'de': 'Sporternährung', 'zh': '运动营养'},
            'Детская развлекательно игровая зона': {'tr': 'Çocuk Eğlence Oyun Alanı',
                                                    'de': 'Kinderunterhaltungsspielzone', 'zh': '儿童娱乐游戏区'},
            'Авто химчистка': {'tr': 'Oto Kuru Temizleme', 'de': 'Autotrockenreinigung', 'zh': '汽车干洗'},
            'Музыкальная студия': {'tr': 'Müzik Stüdyosu', 'de': 'Musikstudio', 'zh': '音乐工作室'},
            'Карго компания': {'tr': 'Kargo Şirketi', 'de': 'Frachtunternehmen', 'zh': '货运公司'},
            'Многопрофильная компания': {'tr': 'Çok Profilli Şirket', 'de': 'Multinationales Unternehmen',
                                         'zh': '多业务公司'},
            'Продовольственная компания': {'tr': 'Gıda Şirketi', 'de': 'Lebensmittelunternehmen', 'zh': '食品公司'},
            'Таможенный брокер': {'tr': 'Gümrük komisyoncusu', 'de': 'Zollmakler', 'zh': '海关经纪人'},
            'Газета': {'tr': 'Gazete', 'de': 'Zeitung', 'zh': '报纸'},
            'Производство лакокрасочных материалов': {'tr': 'Boya ve vernik üretimi',
                                                      'de': 'Herstellung von Lack- und Farbmaterialien',
                                                      'zh': '涂料和颜料制造'},
            'Фото и видео студия': {'tr': 'Fotoğraf ve video stüdyosu', 'de': 'Foto- und Videostudio',
                                    'zh': '照片和视频工作室'},
            'Бухгалтерские услуги': {'tr': 'Muhasebe hizmetleri', 'de': 'Buchhaltungsdienstleistungen', 'zh': '会计服务'},
            'Бар': {'tr': 'Bar', 'de': 'Bar', 'zh': '酒吧'},
            'Производитель стекла': {'tr': 'Cam üreticisi', 'de': 'Glashersteller', 'zh': '玻璃制造商'},
            'Металлоконструкции установка': {'tr': 'Metal konstrüksiyon kurulumu',
                                             'de': 'Metallkonstruktion Installation', 'zh': '金属结构安装'},
            'Производитель Минеральной воды': {'tr': 'Mineral su üreticisi', 'de': 'Mineralwasserhersteller',
                                               'zh': '矿泉水制造商'},
            'Магазин одежды': {'tr': 'Giyim mağazası', 'de': 'Bekleidungsgeschäft', 'zh': '服装店'},
            'Частный детский сад': {'tr': 'Özel anaokulu', 'de': 'Privater Kindergarten', 'zh': '私立幼儿园'},
            'Аренда офисных и торговых площадей': {'tr': 'Ofis ve ticaret alanı kiralama',
                                                   'de': 'Büro- und Geschäftsflächenvermietung', 'zh': '办公和商业区租赁'},
            'Арт-салон сувениров и подарков': {'tr': 'Sanat salonu hediyelik eşya ve hediye',
                                               'de': 'Kunstsalon für Souvenirs und Geschenke', 'zh': '艺术馆纪念品和礼品'},
            'PR агентство': {'tr': 'PR ajansı', 'de': 'PR-Agentur', 'zh': '公关代理'},
            'Кафельные работы': {'tr': 'Fayans işleri', 'de': 'Fliesenarbeiten', 'zh': '瓷砖工程'},
            'Гимназия': {'tr': 'Gimnazyum', 'de': 'Gymnasium', 'zh': '中学'},
            'Строительство дорог': {'tr': 'Yol inşaatı', 'de': 'Straßenbau', 'zh': '道路建设'},
            'Религиозная организация': {'tr': 'Dini örgüt', 'de': 'Religiöse Organisation', 'zh': '宗教组织'},
            'Питомник': {'tr': 'Çocuk bakım evi', 'de': 'Kinderhort', 'zh': '托儿所'},
            'Компания строительных материалов': {'tr': 'İnşaat malzemeleri şirketi',
                                                 'de': 'Bauunternehmung für Baustoffe', 'zh': '建筑材料公司'},
            'Спиртовой завод': {'tr': 'Alkol fabrikası', 'de': 'Spirituosenfabrik', 'zh': '酒精厂'},
            'Автоматизация управленческого и бухгалтерского учета': {'tr': 'Yönetim ve muhasebe otomasyonu',
                                                                     'de': 'Automatisierung von Management- und Buchhaltungssystemen',
                                                                     'zh': '管理和会计自动化'},
            'Авиаперевозки и авиа услуги': {'tr': 'Havayolu taşımacılığı ve hava hizmetleri',
                                            'de': 'Lufttransport und Luftdienstleistungen', 'zh': '航空运输和航空服务'},
            'Строительная компания': {'tr': 'İnşaat şirketi', 'de': 'Bauunternehmen', 'zh': '建筑公司'},
            'Строительство ЛЭП': {'tr': 'Yüksek gerilim hat inşaatı', 'de': 'Hochspannungsleitungsbau',
                                  'zh': '高压输电线路建设'},
            'Производитель снековой продукции': {'tr': 'Atıştırmalık ürün üreticisi',
                                                 'de': 'Hersteller von Snackprodukten', 'zh': '零食制造商'},
            'Мебель кожаная': {'tr': 'Deri mobilya', 'de': 'Ledermöbel', 'zh': '皮革家具'},
            'Бизнес центр': {'tr': 'İş merkezi', 'de': 'Business Center', 'zh': '商务中心'},
            'Родильный дом': {'tr': 'Doğum evi', 'de': 'Geburtshaus', 'zh': '产房'},
            'Сауна': {'tr': 'Sauna', 'de': 'Sauna', 'zh': '桑拿'},
            'Ремонт ходовой': {'tr': 'Süspansiyon tamiri', 'de': 'Fahrwerkreparatur', 'zh': '底盘维修'},
            'Инвестиционный фонд': {'tr': 'Yatırım fonu', 'de': 'Investmentfonds', 'zh': '投资基金'},
            'Туристическое агентство': {'tr': 'Turizm ajansı', 'de': 'Reisebüro', 'zh': '旅行社'},
            'Производитель Энергетических напитков': {'tr': 'Enerji içeceği üreticisi',
                                                      'de': 'Hersteller von Energiegetränken', 'zh': '能量饮料制造商'},
            'Ледовый каток': {'tr': 'Buz pateni pisti', 'de': 'Eislaufbahn', 'zh': '溜冰场'},
            'Стройтехника продажа': {'tr': 'İnşaat makineleri satışı', 'de': 'Verkauf von Baumaschinen',
                                     'zh': '建筑机械销售'},
            'Такси': {'tr': 'Taksi', 'de': 'Taxi', 'zh': '出租车'},
            'Магазин мобильных устройств': {'tr': 'Mobil cihaz mağazası', 'de': 'Geschäft für mobile Geräte',
                                            'zh': '移动设备店'},
            'Камнеобрабатывающая компания': {'tr': 'Taş işleme şirketi', 'de': 'Steinverarbeitungsunternehmen',
                                             'zh': '石材加工公司'},
            'Галерея Керамики': {'tr': 'Seramik galerisi', 'de': 'Keramikgalerie', 'zh': '陶瓷画廊'},
            'Магазин товаров для детей': {'tr': 'Çocuk ürünleri mağazası', 'de': 'Kindergeschäft', 'zh': '儿童用品店'},
            'Салон моды': {'tr': 'Moda salonu', 'de': 'Mode-Salon', 'zh': '时尚沙龙'},
            'Рекламная компания': {'tr': 'Reklam ajansı', 'de': 'Werbefirma', 'zh': '广告公司'},
            'Лесное хозяйство': {'tr': 'Orman işletmesi', 'de': 'Forstwirtschaft', 'zh': '林业'},
            'Швейное производство': {'tr': 'Dikiş üretimi', 'de': 'Nähereiproduktion', 'zh': '缝纫制造'},
            'Архитектурные бюро': {'tr': 'Mimarlık bürosu', 'de': 'Architekturbüro', 'zh': '建筑事务所'},
            'Косметический магазин': {'tr': 'Kozmetik mağazası', 'de': 'Kosmetikgeschäft', 'zh': '化妆品店'},
            'Бытовой сервис': {'tr': 'Ev servisi', 'de': 'Haushaltsdienst', 'zh': '家政服务'},
            'Горнорудная добыча и переработка': {'tr': 'Madencilik ve işleme', 'de': 'Bergbau und Verarbeitung',
                                                 'zh': '矿石采矿和加工'},
            'Полиуретановые конструкции': {'tr': 'Poliüretan konstrüksiyonlar', 'de': 'Polyurethan-Konstruktionen',
                                           'zh': '聚氨酯结构'},
            'Магазин строительных материалов': {'tr': 'İnşaat malzemeleri mağazası', 'de': 'Baumarkt', 'zh': '建筑材料店'},
            'Диски и шины': {'tr': 'Jantlar ve lastikler', 'de': 'Räder und Reifen', 'zh': '轮毂和轮胎'},
            'Ювелирная ассоциация': {'tr': 'Mücevherat derneği', 'de': 'Schmuckverband', 'zh': '珠宝协会'},
            'Интернет-магазин': {'tr': 'İnternet mağazası', 'de': 'Online-Shop', 'zh': '在线商店'},
            'Сырная компания': {'tr': 'Peynir şirketi', 'de': 'Käserei', 'zh': '奶酪公司'},
            'Растениеводческое предприятие': {'tr': 'Bitki yetiştirme şirketi', 'de': 'Pflanzenzuchtunternehmen',
                                              'zh': '植物培育公司'},
            'Ветеринарный центр': {'tr': 'Veteriner merkezi', 'de': 'Tierarztpraxis', 'zh': '兽医中心'},
            'Бассейн': {'tr': 'Havuz', 'de': 'Schwimmbad', 'zh': '游泳池'},
            'Коммунальные служба': {'tr': 'Belediye Hizmetleri', 'de': 'Kommunaldienste', 'zh': '公用事业'},
            'Кардиологический центр': {'tr': 'Kardiyoloji Merkezi', 'de': 'Kardiologisches Zentrum', 'zh': '心脏诊所'},
            'Авторынок': {'tr': 'Araç Pazarı', 'de': 'Fahrzeugmarkt', 'zh': '二手车市场'},
            'Пассажирские перевозки': {'tr': 'Yolcu Taşımacılığı', 'de': 'Personenbeförderung', 'zh': '客运'},
            'Театр': {'tr': 'Tiyatro', 'de': 'Theater', 'zh': '剧院'},
            'Ателье': {'tr': 'Terzi Atölyesi', 'de': 'Atelier', 'zh': '裁缝店'},
            'Магазин хозяйственных товаров': {'tr': 'Ev Ürünleri Mağazası', 'de': 'Haushaltswarengeschäft',
                                              'zh': '家居用品店'},
            'Спортивное кафе': {'tr': 'Spor Kafe', 'de': 'Sportcafé', 'zh': '运动咖啡馆'},
            'Магазин аксессуаров': {'tr': 'Aksesuar Mağazası', 'de': 'Accessoire-Geschäft', 'zh': '配饰店'},
            'Магазин телефонов и гаджетов': {'tr': 'Telefon ve Gadget Mağazası', 'de': 'Handy- und Gadget-Geschäft',
                                             'zh': '手机和小工具店'},
            'Полиграфия': {'tr': 'Poligrafi', 'de': 'Druckerei', 'zh': '印刷业'},
            'Музыкальный магазин': {'tr': 'Müzik Mağazası', 'de': 'Musikgeschäft', 'zh': '音乐店'},
            'Аквапарк': {'tr': 'Su Parkı', 'de': 'Wasserpark', 'zh': '水上公园'},
            'Мебель реставрация': {'tr': 'Mobilya Restorasyonu', 'de': 'Möbelrestaurierung', 'zh': '家具修复'},
            'Производитель Питьевой воды': {'tr': 'İçme Suyu Üreticisi', 'de': 'Trinkwasserhersteller', 'zh': '饮用水生产商'},
            'Рейтинговое агентство': {'tr': 'Derecelendirme Ajansı', 'de': 'Bewertungsagentur', 'zh': '评级机构'},
            'Сельскохозяйственная магазин': {'tr': 'Tarım Mağazası', 'de': 'Landwirtschaftsgeschäft', 'zh': '农产品店'},
            'Трикотажное производство': {'tr': 'Triko Üretimi', 'de': 'Strickwarenproduktion', 'zh': '针织品制造'},
            'Метало работы': {'tr': 'Metal İşleri', 'de': 'Metallarbeiten', 'zh': '金属工程'},
            'Коньячный Завод': {'tr': 'Konjak Fabrikası', 'de': 'Cognac-Fabrik', 'zh': '白兰地工厂'},
            'Охотничье хозяйство': {'tr': 'Av İşletmesi', 'de': 'Jagdbetrieb', 'zh': '狩猎场'},
            'Магазин фурнитуры': {'tr': 'Mobilya Aksesuar Mağazası', 'de': 'Möbelzubehörgeschäft', 'zh': '家具配件店'},
            'Партия': {'tr': 'Parti', 'de': 'Partei', 'zh': '党派'},
            'Стяжка полов': {'tr': 'Zemin Tesviye', 'de': 'Bodenbeschichtung', 'zh': '地板砂浆'},
            'Сварщик': {'tr': 'Kaynakçı', 'de': 'Schweißer', 'zh': '焊工'},
            'Мебель сборка': {'tr': 'Mobilya Montajı', 'de': 'Möbelmontage', 'zh': '家具安装'},
            'Пенсионный фонд': {'tr': 'Emeklilik Fonu', 'de': 'Rentenfonds', 'zh': '养老基金'},
            'Туристическая компания': {'tr': 'Turizm Şirketi', 'de': 'Reiseunternehmen', 'zh': '旅游公司'},
            'Спортивная федерация': {'tr': 'Spor Federasyonu', 'de': 'Sportverband', 'zh': '体育联盟'},
            'Университет': {'tr': 'Üniversite', 'de': 'Universität', 'zh': '大学'},
            'Детский сад и ясли': {'tr': 'Kreş ve Gündüz Bakımevi', 'de': 'Kindergarten und Krippe', 'zh': '幼儿园和托儿所'},
            'Общественное объединение': {'tr': 'Sivil Toplum Kuruluşu', 'de': 'Gemeinnützige Organisation',
                                         'zh': '社会组织'},
            'Автобаза': {'tr': 'Oto Filo Merkezi', 'de': 'Autobasis', 'zh': '汽车基地'},
            'Уход за престарелыми': {'tr': 'Yaşlı Bakımı', 'de': 'Altenpflege', 'zh': '老年护理'},
            'Агентство недвижимости': {'tr': 'Emlak Ajansı', 'de': 'Immobilienagentur', 'zh': '房地产中介'},
            'Продукты питания': {'tr': 'Gıda Ürünleri', 'de': 'Lebensmittel', 'zh': '食品'},
            'Банк': {'tr': 'Banka', 'de': 'Bank', 'zh': '银行'},
            'Силиконовые изделия': {'tr': 'Silikon Ürünleri', 'de': 'Silikonprodukte', 'zh': '硅胶制品'},
            'Производство дверей': {'tr': 'Kapı Üretimi', 'de': 'Türproduktion', 'zh': '门制造'},
            'Паркетные полы': {'tr': 'Parke Zemin', 'de': 'Parkettböden', 'zh': '复合地板'},
            'Детский образовательный центр': {'tr': 'Çocuk Eğitim Merkezi', 'de': 'Kinderbildungscenter',
                                              'zh': '儿童教育中心'},
            'Парк развлечений': {'tr': 'Eğlence Parkı', 'de': 'Vergnügungspark', 'zh': '游乐园'},
            'Организация Выставки, Экспозиции, Ярмарки': {'tr': 'Fuar, Sergi, Pazar Organizasyonu',
                                                          'de': 'Messe-, Ausstellungs- und Marktorganisation',
                                                          'zh': '展览、博览会和市场组织'},
            'Контент-провайдер': {'tr': 'İçerik Sağlayıcı', 'de': 'Content-Provider', 'zh': '内容提供商'},
            'Кожгалантерейное производство': {'tr': 'Deri Ürünleri Üretimi', 'de': 'Lederwarenproduktion',
                                              'zh': '皮革制品生产'},
            'Гостиница': {'tr': 'Otel', 'de': 'Hotel', 'zh': '酒店'},
            'Кузовщик': {'tr': 'Kasa Tamircisi', 'de': 'Karosseriebauer', 'zh': '车身修理工'},
            'Брачное агентство': {'tr': 'Evlenme Ajansı', 'de': 'Heiratsagentur', 'zh': '婚介所'},
            'Оценщики бизнеса': {'tr': 'İş Değerleme Uzmanları', 'de': 'Unternehmensbewerter', 'zh': '商业评估师'},
            'Психологический центр': {'tr': 'Psikoloji Merkezi', 'de': 'Psychologisches Zentrum', 'zh': '心理中心'},
            'Магазины рыболовных товаров': {'tr': 'Balıkçılık Malzemeleri Mağazaları',
                                            'de': 'Angelausrüstungsgeschäfte', 'zh': '钓鱼用品商店'},
            'Магазин для взрослых': {'tr': 'Yetişkin Mağazası', 'de': 'Erwachsenengeschäft', 'zh': '成人用品店'},
            'Магазин средств связи': {'tr': 'İletişim Malzemeleri Mağazası', 'de': 'Kommunikationsausrüstungsgeschäft',
                                      'zh': '通讯设备店'},
            'Оружейный магазин': {'tr': 'Silah Mağazası', 'de': 'Waffengeschäft', 'zh': '武器商店'},
            'Компания производитель удобрений': {'tr': 'Gübre Üretici Şirket', 'de': 'Düngerhersteller',
                                                 'zh': '肥料生产公司'},
            'ЗАГС': {'tr': 'Nüfus Müdürlüğü', 'de': 'Standesamt', 'zh': '人口登记处'},
            'Интернет издания': {'tr': 'İnternet Yayınları', 'de': 'Internetveröffentlichungen', 'zh': '互联网出版物'},
            'Магазин 18+': {'tr': '18+ Mağaza', 'de': '18+ Laden', 'zh': '18+商店'},
            'Производитель тароупаковочной продукции': {'tr': 'Torba Ambalaj Üretici Şirket',
                                                        'de': 'Hersteller von Verpackungsbeuteln', 'zh': '塑料袋生产商'},
            'Фито центр': {'tr': 'Bitki Merkezi', 'de': 'Pflanzenzentrum', 'zh': '植物中心'},
            'Киностудия': {'tr': 'Film Stüdyosu', 'de': 'Filmstudio', 'zh': '电影制片厂'},
            'Электрооборудование': {'tr': 'Elektrik Ekipmanları', 'de': 'Elektroausrüstung', 'zh': '电气设备'},
            'Тренировочный бассейн': {'tr': 'Eğitim Havuzu', 'de': 'Trainingsbecken', 'zh': '培训游泳池'},
            'Коттеджный городок': {'tr': 'Kır Evi Köyü', 'de': 'Cottage-Siedlung', 'zh': '别墅小区'},
            'Магазин интимных вещей': {'tr': 'Düşkünler Dükkanı', 'de': 'Intimgeschäft', 'zh': '私密物品商店'},
            'Фракция': {'tr': 'Fraksiyon', 'de': 'Fraktion', 'zh': '派系'},
            'Психиатрия': {'tr': 'Psikiyatri', 'de': 'Psychiatrie', 'zh': '精神病学'},
            'Охранное агентство': {'tr': 'Güvenlik Ajansı', 'de': 'Sicherheitsagentur', 'zh': '保安公司'},
            'Радиокомпания': {'tr': 'Radyo Şirketi', 'de': 'Radiogesellschaft', 'zh': '广播公司'},
            'Модный салон': {'tr': 'Moda Salonu', 'de': 'Modischer Salon', 'zh': '时尚沙龙'},
            'Языковые курсы': {'tr': 'Dil Kursları', 'de': 'Sprachkurse', 'zh': '语言课程'},
            'ЖД агентство доставки': {'tr': 'Demiryolu Taşıma Ajansı', 'de': 'Eisenbahnzustellagentur', 'zh': '铁路运输代理'},
            'Ковровое производство': {'tr': 'Halı Üretimi', 'de': 'Teppichherstellung', 'zh': '地毯生产'},
            'Ночной бар': {'tr': 'Gece Barı', 'de': 'Nachtbar', 'zh': '夜吧'},
            'Интернет агентство': {'tr': 'İnternet Ajansı', 'de': 'Internetagentur', 'zh': '互联网代理'},
            'Караоке центр': {'tr': 'Karaoke Merkezi', 'de': 'Karaoke-Zentrum', 'zh': '卡拉OK中心'},
            'Компьютерная компания': {'tr': 'Bilgisayar Şirketi', 'de': 'Computerunternehmen', 'zh': '计算机公司'},
            'Юридическая организация': {'tr': 'Hukuk Organizasyonu', 'de': 'Juristische Organisation', 'zh': '法律组织'},
            'Детская развлекательно игровая площадка': {'tr': 'Çocuk Eğlence ve Oyun Alanı',
                                                        'de': 'Kinderunterhaltungs- und Spielplatz', 'zh': '儿童娱乐游乐场'},
            'Другие сферы медицины и здоровья': {'tr': 'Diğer Tıp ve Sağlık Alanları',
                                                 'de': 'Andere Bereiche der Medizin und Gesundheit', 'zh': '其他医学和健康领域'},
            'Кулинарная фабрика': {'tr': 'Mutfak Fabrikası', 'de': 'Kulinarische Fabrik', 'zh': '烹饪工厂'},
            'Магазин электротехники': {'tr': 'Elektronik Mağaza', 'de': 'Elektronikgeschäft', 'zh': '电器店'},
            'Цирк': {'tr': 'Sirk', 'de': 'Zirkus', 'zh': '马戏团'},
            'Оценка недвижимости': {'tr': 'Emlak Değerlendirme', 'de': 'Immobilienbewertung', 'zh': '房地产评估'},
            'Заказ и доставка готовых блюд': {'tr': 'Yemek Siparişi ve Teslimat',
                                              'de': 'Bestellung und Lieferung von Fertiggerichten', 'zh': '订购和送餐'},
            'Производство из меха': {'tr': 'Kürk Üretimi', 'de': 'Pelzproduktion', 'zh': '毛皮生产'},
            'Промышленные товары': {'tr': 'Endüstriyel Ürünler', 'de': 'Industriegüter', 'zh': '工业品'},
            'Художественная школа': {'tr': 'Sanat Okulu', 'de': 'Kunstschule', 'zh': '艺术学校'},
            'Тренажёрный зал': {'tr': 'Spor Salonu', 'de': 'Fitnessstudio', 'zh': '健身房'},
            'Маркетинговые услуги': {'tr': 'Pazarlama Hizmetleri', 'de': 'Marketingdienstleistungen', 'zh': '营销服务'},
            'АЗС': {'tr': 'Otomatik Akaryakıt İstasyonu', 'de': 'Tankstelle', 'zh': '加油站'},
            'Домовой поселок': {'tr': 'Evsiz Köy', 'de': 'Häuserdorf', 'zh': '住宅区'},
            'Промышленное строительство': {'tr': 'Endüstriyel İnşaat', 'de': 'Industriebau', 'zh': '工业建筑'},
            'Пасека': {'tr': 'Arı Kovanı', 'de': 'Bienenstock', 'zh': '蜂场'},
            'Разработка программного обеспечения': {'tr': 'Yazılım Geliştirme', 'de': 'Softwareentwicklung',
                                                    'zh': '软件开发'},
            'Магазин у дома': {'tr': 'Evde Mağaza', 'de': 'Laden in der Nähe', 'zh': '家门口商店'},
            'Образование за рубежом': {'tr': 'Yurtdışında Eğitim', 'de': 'Bildung im Ausland', 'zh': '海外教育'},
            'Молочная компания': {'tr': 'Süt Şirketi', 'de': 'Milchunternehmen', 'zh': '乳制品公司'},
            'Производитель безалкогольных напитков': {'tr': 'Alkolsüz İçecek Üreticisi',
                                                      'de': 'Hersteller von alkoholfreien Getränken', 'zh': '无酒精饮料生产商'},
            'Реставрация одежды': {'tr': 'Giyim Restorasyonu', 'de': 'Kleidungsrestaurierung', 'zh': '服装修复'},
            'Биосферная зона': {'tr': 'Biyosfer Bölgesi', 'de': 'Biosphärenzone', 'zh': '生物圈区域'},
            'Пункт замены масел и другое': {'tr': 'Yağ Değiştirme Noktası ve Diğerleri',
                                            'de': 'Ölwechselstelle und mehr', 'zh': '更换机油点等'},
            'Жилой комплекс': {'tr': 'Konut Kompleksi', 'de': 'Wohnkomplex', 'zh': '住宅区'},
            'Литье и производство метала': {'tr': 'Döküm ve Metal Üretimi', 'de': 'Gießen und Metallproduktion',
                                            'zh': '铸造和金属生产'},
            'Полиуретановые изделия': {'tr': 'Poliüretan Ürünleri', 'de': 'Polyurethanprodukte', 'zh': '聚氨酯制品'},
            'Магазин спецодежды и средств защиты': {'tr': 'Özel Giyim ve Koruyucu Malzeme Mağazası',
                                                    'de': 'Spezialbekleidungs- und Schutzausrüstungsgeschäft',
                                                    'zh': '特殊服装和防护用品商店'},
            'Медицинский центр': {'tr': 'Tıp Merkezi', 'de': 'Medizinisches Zentrum', 'zh': '医疗中心'},
            'Производитель полуфабрикатов': {'tr': 'Yarı Mamul Ürün Üreticisi',
                                             'de': 'Hersteller von Halbfertigprodukten', 'zh': '半成品制造商'},
            'Метало конструкции': {'tr': 'Metal Konstrüksiyon', 'de': 'Metallkonstruktionen', 'zh': '金属结构'},
            'Производитель соков и сокосодержащих напитков': {'tr': 'Meyve Suyu ve İçecek Üreticisi',
                                                              'de': 'Hersteller von Säften und Saftgetränken',
                                                              'zh': '果汁和含果汁饮料生产商'},
            'Ювелирная компания': {'tr': 'Mücevher Şirketi', 'de': 'Schmuckunternehmen', 'zh': '珠宝公司'},
            'Галерея штор': {'tr': 'Perde Galerisi', 'de': 'Vorhanggalerie', 'zh': '窗帘画廊'},
            'Другие сферы бизнеса': {'tr': 'Diğer İş Alanları', 'de': 'Andere Geschäftsbereiche', 'zh': '其他商业领域'},
            'Хладокомбинат': {'tr': 'Soğuk Hava Birliği', 'de': 'Kühlkombinat', 'zh': '冷库联合'},
            'Покраска кузова': {'tr': 'Gövde Boyama', 'de': 'Karosserielackierung', 'zh': '车身喷漆'},
            'Транспортные услуги': {'tr': 'Taşıma Hizmetleri', 'de': 'Transportdienstleistungen', 'zh': '运输服务'},
            'Консалтинговая компания': {'tr': 'Danışmanlık Şirketi', 'de': 'Beratungsunternehmen', 'zh': '咨询公司'},
            'Производитель стеклотары': {'tr': 'Cam Ürünleri Üreticisi', 'de': 'Hersteller von Glasverpackungen',
                                         'zh': '玻璃制品生产商'},
            'Родильный центр': {'tr': 'Doğum Merkezi', 'de': 'Geburtszentrum', 'zh': '分娩中心'},
            'Музыкальные инструменты магазин': {'tr': 'Müzik Aletleri Mağazası', 'de': 'Musikinstrumente Laden',
                                                'zh': '乐器商店'},
            'Текстильное производство': {'tr': 'Tekstil Üretimi', 'de': 'Textilproduktion', 'zh': '纺织品生产'},
            'Поставщик зеркал': {'tr': 'Ayna Tedarikçisi', 'de': 'Spiegelanbieter', 'zh': '镜子供应商'},
            'Ювелирный магазин': {'tr': 'Mücevher mağazası', 'de': 'Juweliergeschäft', 'zh': '珠宝商店'},
            'Агентство сертификации': {'tr': 'Sertifikasyon ajansı', 'de': 'Zertifizierungsagentur', 'zh': '认证机构'},
            'Частный диспансер': {'tr': 'Özel poliklinik', 'de': 'Private Ambulanz', 'zh': '私人门诊'},
            'Вулканизация': {'tr': 'Vulkanizasyon', 'de': 'Vulkanisierung', 'zh': '硫化'},
            'Оздоровительный центр': {'tr': 'Sağlık merkezi', 'de': 'Erholungszentrum', 'zh': '康复中心'},
            'Музыкальное заведение': {'tr': 'Müzik mekanı', 'de': 'Musikgeschäft', 'zh': '音乐场所'},
            'Контент студия': {'tr': 'İçerik stüdyosu', 'de': 'Content-Studio', 'zh': '内容工作室'},
            'Винный завод': {'tr': 'Şarap fabrikası', 'de': 'Weingut', 'zh': '酒厂'},
            'Музей': {'tr': 'Müze', 'de': 'Museum', 'zh': '博物馆'},
            'Ассоциация': {'tr': 'Dernek', 'de': 'Verband', 'zh': '协会'},
            'Магазин труб и отопления': {'tr': 'Boru ve ısıtma mağazası', 'de': 'Rohr- und Heizungsgeschäft',
                                         'zh': '管道和供暖器材商店'},
            'Поставщик полиэтиленовых изделий': {'tr': 'Polietilen ürün tedarikçisi',
                                                 'de': 'Lieferant von Polyethylenprodukten', 'zh': '聚乙烯制品供应商'},
            'Металлоконструкции производство и сборка': {'tr': 'Metal konstrüksiyon üretim ve montaj',
                                                         'de': 'Metallkonstruktion Herstellung und Montage',
                                                         'zh': '金属构件制造和装配'},
            'Информационная служба': {'tr': 'Bilgi servisi', 'de': 'Informationsdienst', 'zh': '信息服务'},
            'Золотодобывающая компания': {'tr': 'Altın madenciliği şirketi', 'de': 'Goldabbauunternehmen',
                                          'zh': '黄金采矿公司'},
            'Кредитный союз': {'tr': 'Kredi birliği', 'de': 'Kreditgenossenschaft', 'zh': '信用社'},
            'Парикмахерская': {'tr': 'Berber dükkanı', 'de': 'Frisörsalon', 'zh': '理发店'},
            'Горнолыжная база': {'tr': 'Kayak merkezi', 'de': 'Ski-Basis', 'zh': '滑雪基地'},
            'Мебель корпусная': {'tr': 'Modüler mobilya', 'de': 'Korpusmöbel', 'zh': '模块家具'},
            'Общественный фонд': {'tr': 'Sivil toplum fonu', 'de': 'Gemeinnütziger Fonds', 'zh': '社会基金'},
            'Автокожа и салон': {'tr': 'Otomobil derisi ve salonu', 'de': 'Autoleder und Innenausstattung',
                                 'zh': '汽车皮革和内饰'},
            'Жалюзи': {'tr': 'Jaluzi', 'de': 'Jalousie', 'zh': '百叶窗'},
            'Строительство мостов': {'tr': 'Köprü inşaatı', 'de': 'Brückenbau', 'zh': '桥梁建设'},
            'Зоопарк': {'tr': 'Hayvanat bahçesi', 'de': 'Zoo', 'zh': '动物园'},
            'Производитель кондитерских изделий': {'tr': 'Şekerleme üreticisi', 'de': 'Süßwarenhersteller',
                                                   'zh': '糖果制造商'},
            'Организация банкетов и фуршетов': {'tr': 'Banket ve kokteyl organizasyonu',
                                                'de': 'Veranstaltung von Banketten und Empfängen', 'zh': '宴会和酒会组织'},
            'Фермерское хозяйство': {'tr': 'Çiftlik', 'de': 'Bauernhof', 'zh': '农场'},
            'Железнодорожные перевозки': {'tr': 'Demiryolu taşımacılığı', 'de': 'Eisenbahntransport', 'zh': '铁路运输'},
            'Магазин кафеля': {'tr': 'Seramik mağazası', 'de': 'Fliesenladen', 'zh': '瓷砖商店'},
            'Магазин автозапчастей': {'tr': 'Oto yedek parça mağazası', 'de': 'Autoteileladen', 'zh': '汽车零部件商店'},
            'Галерея обоев': {'tr': 'Duvar kağıdı galerisi', 'de': 'Tapetengalerie', 'zh': '壁纸画廊'},
            'Организация проведение праздничных мероприятий, концертов, шоу-программ': {
                'tr': 'Tatil etkinlikleri, konserler, şov programları düzenleme',
                'de': 'Veranstaltung von Feierlichkeiten, Konzerten, Showprogrammen', 'zh': '节日活动，音乐会，演出节目组织'},
            'Помощь за детьми': {'tr': 'Çocuk bakımı', 'de': 'Kinderbetreuung', 'zh': '儿童护理'},
            'Ювелирный салон': {'tr': 'Mücevher salonu', 'de': 'Juweliersalon', 'zh': '珠宝沙龙'},
            'Спутниковые системы, GPS - мониторинг автомобилей': {'tr': 'Uydu sistemleri, GPS - araç izleme',
                                                                  'de': 'Satellitensysteme, GPS-Fahrzeugüberwachung',
                                                                  'zh': '卫星系统，GPS-车辆监控'},
            'Пивоварня': {'tr': 'Bira fabrikası', 'de': 'Brauerei', 'zh': '啤酒厂'},
            'Магазин спортивной обуви': {'tr': 'Spor ayakkabı mağazası', 'de': 'Sportgeschäft für Schuhe',
                                         'zh': '运动鞋商店'},
            'Блогер': {'tr': 'Blogger', 'de': 'Blogger', 'zh': '博客作者'},
            'Крипто компания': {'tr': 'Kripto şirket', 'de': 'Krypto-Unternehmen', 'zh': '加密公司'},
            'Аварийные служба': {'tr': 'Acil servis', 'de': 'Notdienst', 'zh': '紧急服务'},
            'Юридическая компания': {'tr': 'Hukuk firması', 'de': 'Rechtsanwaltskanzlei', 'zh': '法律公司'},
            'Производство спецодежды и униформы': {'tr': 'Özel giyim ve üniforma üretimi',
                                                   'de': 'Produktion von Arbeitskleidung und Uniformen',
                                                   'zh': '特种服装和制服制造'},
            'Сберегательная касса': {'tr': 'Tasarruf kasası', 'de': 'Sparkasse', 'zh': '储蓄银行'},
            'Детский лагерь': {'tr': 'Çocuk kampı', 'de': 'Kinderlager', 'zh': '儿童营地'},
            'Производитель Вина': {'tr': 'Şarap üreticisi', 'de': 'Weinhersteller', 'zh': '葡萄酒制造商'},
            'Профсоюз': {'tr': 'Sendika', 'de': 'Gewerkschaft', 'zh': '工会'},
            'Караоке клуб': {'tr': 'Karaoke kulübü', 'de': 'Karaoke-Club', 'zh': '卡拉OK俱乐部'},
            'Нарезка зеркал': {'tr': 'Ayna kesimi', 'de': 'Spiegelzuschnitt', 'zh': '镜子切割'},
            'Спортшкола': {'tr': 'Spor okulu', 'de': 'Sportschule', 'zh': '体育学校'},
            'Салон красоты': {'tr': 'Güzellik salonu', 'de': 'Schönheitssalon', 'zh': '美容沙龙'},
            'Сельхозпроизводитель': {'tr': 'Tarım üreticisi', 'de': 'Landwirtschaftsproduzent', 'zh': '农业生产商'},
            'Табачная фабрика': {'tr': 'Tütün fabrikası', 'de': 'Tabakfabrik', 'zh': '烟草工厂'},
            'Теннис': {'tr': 'Tenis', 'de': 'Tennis', 'zh': '网球'},
            'Магазин деревянных товаров': {'tr': 'Ahşap ürün mağazası', 'de': 'Holzwarengeschäft', 'zh': '木制品商店'},
            'Рынок': {'tr': 'Pazar', 'de': 'Markt', 'zh': '市场'},
            'Химчистки и прачечные': {'tr': 'Kuru temizleme ve çamaşırhane', 'de': 'Reinigung und Wäscherei',
                                      'zh': '干洗和洗衣店'},
            'Веб-дизайн': {'tr': 'Web tasarım', 'de': 'Webdesign', 'zh': '网页设计'},
            'Фонд': {'tr': 'Vakıf', 'de': 'Fond', 'zh': '基金'},
            'Фото студия': {'tr': 'Fotoğraf stüdyosu', 'de': 'Fotostudio', 'zh': '摄影工作室'},
            'Силиконовые формы': {'tr': 'Silikon kalıplar', 'de': 'Silikonformen', 'zh': '硅胶模具'},
            'Бумажное производство: тара, упаковка, бумажная продукция': {
                'tr': 'Kağıt üretimi: ambalaj, paketleme, kağıt ürünleri',
                'de': 'Papierproduktion: Verpackung, Verpackung, Papierprodukte', 'zh': '纸制品制造：包装，包装，纸制品'},
            'Электромонтажные работы': {'tr': 'Elektrik Montaj İşleri', 'de': 'Elektroinstallation', 'zh': '电气安装'},
            'Продуктовый склад': {'tr': 'Gıda Deposu', 'de': 'Lebensmittellager', 'zh': '食品仓库'},
            'Библиотека': {'tr': 'Kütüphane', 'de': 'Bibliothek', 'zh': '图书馆'},
            'Журнал': {'tr': 'Dergi', 'de': 'Zeitschrift', 'zh': '杂志'},
            'Религиозная школа': {'tr': 'Din Okulu', 'de': 'Religiöse Schule', 'zh': '宗教学校'},
            'Металлообработка производство': {'tr': 'Metal İşleme Üretimi', 'de': 'Metallverarbeitung Produktion',
                                              'zh': '金属加工生产'},
            'Аудиторские услуги': {'tr': 'Denetim Hizmetleri', 'de': 'Wirtschaftsprüfungsdienstleistungen',
                                   'zh': '审计服务'},
            'Микрокредитная компания': {'tr': 'Mikrokredi Şirketi', 'de': 'Mikrokreditunternehmen', 'zh': '小额信贷公司'},
            'Пункт приема платежей': {'tr': 'Ödeme Noktası', 'de': 'Zahlungsstelle', 'zh': '收款点'},
            'Суши кафе': {'tr': 'Sushi Kafe', 'de': 'Sushi Café', 'zh': '寿司咖啡馆'},
            'Ударные и бросковые единоборства': {'tr': 'Dövüş Sanatları', 'de': 'Kampfsportarten', 'zh': '搏击运动'},
            'Контент компания': {'tr': 'İçerik Şirketi', 'de': 'Content-Unternehmen', 'zh': '内容公司'},
            'Изготовление штампов, печатей и номерных знаков': {'tr': 'Mühür ve Damga Üretimi',
                                                                'de': 'Stempel- und Siegelherstellung',
                                                                'zh': '印章、印章和编号制造'},
            'Авиа агентство доставки': {'tr': 'Havayolu Taşıma Ajansı', 'de': 'Luftfrachtagentur', 'zh': '航空货运代理'},
            'Ретейл компания': {'tr': 'Perakende Şirketi', 'de': 'Einzelhandelsunternehmen', 'zh': '零售公司'},
            'Химические материалы - производство, продажа': {'tr': 'Kimyasal Malzeme Üretimi ve Satışı',
                                                             'de': 'Chemische Materialien Herstellung und Verkauf',
                                                             'zh': '化学材料生产和销售'},
            'Ивент агентство': {'tr': 'Etkinlik Ajansı', 'de': 'Event-Agentur', 'zh': '活动代理'},
            'Художественное училище': {'tr': 'Sanat Okulu', 'de': 'Kunstschule', 'zh': '艺术学校'},
            'Канализационные работы': {'tr': 'Kanalizasyon Çalışmaları', 'de': 'Kanalisation Arbeiten', 'zh': '排水工程'},
            'Консалтинговые услуги': {'tr': 'Danışmanlık Hizmetleri', 'de': 'Beratungsdienstleistungen', 'zh': '咨询服务'},
            'Ландшафтная компания': {'tr': 'Peyzaj Şirketi', 'de': 'Landschaftsunternehmen', 'zh': '园林公司'},
            'It компания': {'tr': 'IT Şirketi', 'de': 'IT-Unternehmen', 'zh': 'IT公司'},
            'Ремонт обуви': {'tr': 'Ayakkabı Tamiri', 'de': 'Schuhreparatur', 'zh': '鞋类修理'},
            'Роллер клуб': {'tr': 'Kaykay Kulübü', 'de': 'Roller-Club', 'zh': '轮滑俱乐部'},
            'Агентство по недвижимости': {'tr': 'Emlak Ajansı', 'de': 'Immobilienagentur', 'zh': '房地产代理'},
            'Алко завод': {'tr': 'Alkol Fabrikası', 'de': 'Alkoholfabrik', 'zh': '酒厂'},
            'Стройтехника аренда': {'tr': 'İnşaat Makine Kiralama', 'de': 'Baumaschinenverleih', 'zh': '建筑机械租赁'},
            'Магазин Металла': {'tr': 'Metal Mağaza', 'de': 'Metallgeschäft', 'zh': '金属商店'},
            'Банный комплекс': {'tr': 'Sauna Kompleksi', 'de': 'Badekomplex', 'zh': '桑拿综合设施'},
            'Телерадиокомпания': {'tr': 'Televizyon ve Radyo Şirketi', 'de': 'Fernseh- und Radiounternehmen',
                                  'zh': '电视和广播公司'},
            'Пекарня': {'tr': 'Fırın', 'de': 'Bäckerei', 'zh': '面包店'},
            'Натяжные потолки': {'tr': 'Asma Tavanlar', 'de': 'Spanndecken', 'zh': '吊顶'},
            'Мебель эксклюзивная': {'tr': 'Özel Mobilya', 'de': 'Exklusive Möbel', 'zh': '独家家具'},
            'Парфюмерный магазин': {'tr': 'Parfüm Mağazası', 'de': 'Parfümerie', 'zh': '香水店'},
            'Интернет-провайдер': {'tr': 'İnternet Sağlayıcı', 'de': 'Internetanbieter', 'zh': '互联网提供商'},
            'Проектный институт': {'tr': 'Proje Enstitüsü', 'de': 'Planungsinstitut', 'zh': '设计研究所'},
            'Ремонт ювелирных изделий': {'tr': 'Mücevherat Tamiri', 'de': 'Schmuckreparatur', 'zh': '珠宝修理'},
            'Автопредприятие': {'tr': 'Otomotiv Şirketi', 'de': 'Autounternehmen', 'zh': '汽车公司'},
            'Газовая компания': {'tr': 'Gaz Şirketi', 'de': 'Gasunternehmen', 'zh': '燃气公司'},
            'Железобетонные конструкции': {'tr': 'Demir Beton Yapılar', 'de': 'Stahlbetonkonstruktionen',
                                           'zh': '钢筋混凝土结构'},
            'Магазин спиртного': {'tr': 'Alkollü İçki Mağazası', 'de': 'Spirituosenladen', 'zh': '酒类商店'},
            'Автозвук': {'tr': 'Oto Ses Sistemi', 'de': 'Car Audio', 'zh': '汽车音响'},
            'Картографическая компания': {'tr': 'Harita Şirketi', 'de': 'Kartografieunternehmen', 'zh': '地图公司'},
            'Автохимия': {'tr': 'Oto Kimyasal', 'de': 'Autopflegeprodukte', 'zh': '汽车化学产品'},
            'Заповедник': {'tr': 'Doğa Koruma Alanı', 'de': 'Naturschutzgebiet', 'zh': '自然保护区'},
            'Производство комбинированных кормов': {'tr': 'Karma Yem Üretimi', 'de': 'Mischfutterproduktion',
                                                    'zh': '混合饲料生产'},
            'Рабата с камнем': {'tr': 'Taşlı Bahçe Düzenlemesi', 'de': 'Steingarten', 'zh': '石头花园'},
            'ЖД касса': {'tr': 'Demiryolu Gişe', 'de': 'Eisenbahnschalter', 'zh': '铁路售票处'},
            'Производитель табачных изделий': {'tr': 'Tütün Ürünleri Üreticisi', 'de': 'Tabakproduzent',
                                               'zh': '烟草制品生产商'},
            'Производитель винных изделий': {'tr': 'Şarap Üreticisi', 'de': 'Weinproduzent', 'zh': '葡萄酒生产商'},
            'Школа лицей': {'tr': 'Lise Okulu', 'de': 'Gymnasium', 'zh': '高中'},
            'Авто аренда': {'tr': 'Araç Kiralama', 'de': 'Autovermietung', 'zh': '汽车租赁'},
            'Системы телекоммуникаций': {'tr': 'Telekomünikasyon Sistemleri', 'de': 'Telekommunikationssysteme',
                                         'zh': '通信系统'},
            'Спортивный клуб': {'tr': 'Spor Kulübü', 'de': 'Sportverein', 'zh': '体育俱乐部'},
            'Рыбалка': {'tr': 'Balıkçılık', 'de': 'Angeln', 'zh': '钓鱼'},
            'Тонировка': {'tr': 'Cam Filmi Kaplama', 'de': 'Tönung', 'zh': '隔热膜'},
            'Зоомагазин': {'tr': 'Zoo Mağaza', 'de': 'Zoogeschäft', 'zh': '宠物商店'},
            'Овощеводческое хозяйство': {'tr': 'Sebze Üretim Çiftliği', 'de': 'Gemüsebau', 'zh': '蔬菜种植园'},
            'Шторы': {'tr': 'Perdeler', 'de': 'Vorhänge', 'zh': '窗帘'},
            'Пиццерия': {'tr': 'Pizzacı', 'de': 'Pizzeria', 'zh': '比萨店'},
            'Кованные изделия': {'tr': 'Dövme Ürünler', 'de': 'Schmiedeartikel', 'zh': '锻造产品'},
            'Склады замороженной продукции': {'tr': 'Donmuş Ürün Deposu', 'de': 'Gefrierlager', 'zh': '冷冻产品仓库'},
            'Инструменты для авто': {'tr': 'Araç Araçları', 'de': 'Auto Werkzeuge', 'zh': '汽车工具'},
            'Пивной завод': {'tr': 'Bira Fabrikası', 'de': 'Brauerei', 'zh': '啤酒厂'},
            'Суши бар': {'tr': 'Suşi Bar', 'de': 'Sushi-Bar', 'zh': '寿司吧'},
            'Мучные изделия': {'tr': 'Unlu Mamuller', 'de': 'Mehlprodukte', 'zh': '面粉制品'},
            'Спортивное объединение': {'tr': 'Spor Birliği', 'de': 'Sportvereinigung', 'zh': '体育组织'},
            'Общеобразовательная школа': {'tr': 'Genel Eğitim Okulu', 'de': 'Allgemeinschule', 'zh': '综合学校'},
            'Игровая студия': {'tr': 'Oyun Stüdyosu', 'de': 'Spielestudio', 'zh': '游戏工作室'},
            'Авто системы': {'tr': 'Oto Sistemleri', 'de': 'Auto Systeme', 'zh': '汽车系统'},
            'Чайная компания': {'tr': 'Çay Şirketi', 'de': 'Teeunternehmen', 'zh': '茶公司'},
            'Кирпичная кладка': {'tr': 'Tuğla Duvar Döşeme', 'de': 'Ziegelmauerwerk', 'zh': '砖砌'},
            'Авто сварка': {'tr': 'Oto Kaynak', 'de': 'Auto Schweißen', 'zh': '汽车焊接'},
            'Танцевальная студия': {'tr': 'Dans Stüdyosu', 'de': 'Tanzstudio', 'zh': '舞蹈工作室'},
            'Спецодежда и униформа': {'tr': 'Özel Giyim ve Üniforma', 'de': 'Berufskleidung und Uniform',
                                      'zh': '特殊服装和制服'},
            'Издательство': {'tr': 'Yayınevi', 'de': 'Verlag', 'zh': '出版社'},
            'Железнодорожная компания': {'tr': 'Demiryolu Şirketi', 'de': 'Eisenbahngesellschaft', 'zh': '铁路公司'},
            'Кондитерский магазин': {'tr': 'Pastane', 'de': 'Konditorei', 'zh': '糖果店'},
            'Бильярдный клуб': {'tr': 'Bilardo Kulübü', 'de': 'Billardclub', 'zh': '台球俱乐部'},
            'Каменные работы': {'tr': 'Taş İşleri', 'de': 'Steinarbeiten', 'zh': '石工作'},
            'Тюнинг центр': {'tr': 'Tuning Merkezi', 'de': 'Tuning Zentrum', 'zh': '改装中心'},
            'Металлопрокат': {'tr': 'Metal Rulo', 'de': 'Metallwalzwerk', 'zh': '金属轧制厂'},
            'Производитель молочной продукции': {'tr': 'Süt Ürünleri Üreticisi', 'de': 'Milchproduzent',
                                                 'zh': '奶制品生产商'},
            'Авиа агентства и авиакассы': {'tr': 'Havayolu Ajansı ve Gişeler', 'de': 'Flugagentur und Schalter',
                                           'zh': '航空代理和售票处'},
            'Фасадные работы': {'tr': 'Cephe Çalışmaları', 'de': 'Fassadenarbeiten', 'zh': '外墙工程'},
            'Производитель зеркал': {'tr': 'Ayna Üreticisi', 'de': 'Spiegelhersteller', 'zh': '镜子制造商'},
            'Семеноводческие хозяйство': {'tr': 'Tohumculuk İşletmesi', 'de': 'Saatgutbetrieb', 'zh': '种子农场'},
            'Солевой завод': {'tr': 'Tuz Fabrikası', 'de': 'Salzfabrik', 'zh': '盐厂'},
            'Готовые двери': {'tr': 'Hazır Kapılar', 'de': 'Fertigtüren', 'zh': '成品门'},
            'Косметологический центр': {'tr': 'Kozmetoloji Merkezi', 'de': 'Kosmetikzentrum', 'zh': '美容中心'},
            'Торгово-развлекательный центр': {'tr': 'Ticaret ve Eğlence Merkezi',
                                              'de': 'Handels- und Unterhaltungszentrum', 'zh': '商业娱乐中心'},
            'Мелиорационное агентство': {'tr': 'Meliorasyon Ajansı', 'de': 'Meliorationsagentur', 'zh': '水土保持机构'},
            'Религиозный цент': {'tr': 'Dini Merkez', 'de': 'Religiöses Zentrum', 'zh': '宗教中心'},
            'Ремонт сотовых телефонов': {'tr': 'Cep Telefonu Onarımı', 'de': 'Handyreparatur', 'zh': '手机维修'},
            'Авиа служба доставки': {'tr': 'Hava Kargo Servisi', 'de': 'Luftfrachtdienst', 'zh': '航空货运服务'},
            'Салон цветов': {'tr': 'Çiçek Salonu', 'de': 'Blumensalon', 'zh': '花店'},
            'Микрофинансовая организация': {'tr': 'Mikrofinans Kuruluşu', 'de': 'Mikrofinanzorganisation',
                                            'zh': '微融资机构'},
            'Адвокат': {'tr': 'Avukat', 'de': 'Anwalt', 'zh': '律师'},
            'Частная больница': {'tr': 'Özel Hastane', 'de': 'Privatklinik', 'zh': '私立医院'},
            'Баня': {'tr': 'Hamam', 'de': 'Sauna', 'zh': '浴室'},
            'Рыбное хозяйство': {'tr': 'Balıkçılık İşletmesi', 'de': 'Fischereibetrieb', 'zh': '渔业公司'},
            'Фитнес клуб': {'tr': 'Fitness Kulübü', 'de': 'Fitnessclub', 'zh': '健身俱乐部'},
            'Магазин мыло моющих средств': {'tr': 'Sabun Mağazası', 'de': 'Seifenladen', 'zh': '肥皂店'},
            'Ковровый магазин': {'tr': 'Halı Mağazası', 'de': 'Teppichladen', 'zh': '地毯店'},
            'Центры социальной сферы': {'tr': 'Sosyal Merkezler', 'de': 'Soziale Einrichtungen', 'zh': '社会服务中心'},
            'Детский сад': {'tr': 'Çocuk Bahçesi', 'de': 'Kindergarten', 'zh': '幼儿园'},
            'Компьютерный магазин': {'tr': 'Bilgisayar Mağazası', 'de': 'Computerladen', 'zh': '电脑店'},
            'Учебный центр': {'tr': 'Eğitim Merkezi', 'de': 'Bildungszentrum', 'zh': '培训中心'},
            'Лотереи': {'tr': 'Loto', 'de': 'Lotterie', 'zh': '彩票'},
            'Другие сферы услуг': {'tr': 'Diğer Hizmet Alanları', 'de': 'Andere Dienstleistungen', 'zh': '其他服务行业'},
            'Курьерская служба': {'tr': 'Kurye Servisi', 'de': 'Kurierdienst', 'zh': '快递服务'},
            'Рафтинг': {'tr': 'Rafting', 'de': 'Rafting', 'zh': '漂流'},
            'Телефонная связь': {'tr': 'Telefon Bağlantısı', 'de': 'Telefonverbindung', 'zh': '电话通讯'},
            'Оптика': {'tr': 'Optik', 'de': 'Optik', 'zh': '光学'},
            'Отель': {'tr': 'Otel', 'de': 'Hotel', 'zh': '酒店'},
            'Частная общеобразовательная школа': {'tr': 'Özel Genel Eğitim Okulu', 'de': 'Private Gesamtschule',
                                                  'zh': '私立综合学校'},
            'Супермаркет': {'tr': 'Süpermarket', 'de': 'Supermarkt', 'zh': '超市'},
            'Шелкография': {'tr': 'İpek Baskı', 'de': 'Siebdruck', 'zh': '丝网印刷'},
            'Макаронная фабрика': {'tr': 'Makarna Fabrikası', 'de': 'Nudelfabrik', 'zh': '面食厂'},
            'Народно художественный промысел': {'tr': 'Halk Sanatı', 'de': 'Volkskunst', 'zh': '民间艺术工艺'},
            'Малярные работы': {'tr': 'Boyama İşleri', 'de': 'Malerarbeiten', 'zh': '油漆工程'},
            'Профилакторий': {'tr': 'Profilaktoryum', 'de': 'Prophylaxe-Einrichtung', 'zh': '保健院'},
            'Образовательный центр': {'tr': 'Eğitim Merkezi', 'de': 'Bildungszentrum', 'zh': '教育中心'},
            'Кофейная компания': {'tr': 'Kahve Şirketi', 'de': 'Kaffeefirma', 'zh': '咖啡公司'},
            'Магазин замков': {'tr': 'Kilit Mağazası', 'de': 'Schlossladen', 'zh': '锁店'},
            'Служба доставки товаров на дом и в офисы': {'tr': 'Ev ve Ofis Teslimat Hizmeti',
                                                         'de': 'Lieferdienst für Haus und Büro', 'zh': '上门和办公室商品送货服务'},
            'Стоматологическая клиника': {'tr': 'Diş Kliniği', 'de': 'Zahnklinik', 'zh': '牙科诊所'},
            'ПП Кафе': {'tr': 'PP Kafe', 'de': 'PP Café', 'zh': 'PP咖啡馆'},
            'Буровые, взрывные, геологические работы': {'tr': 'Delme, Patlatma, Jeolojik Çalışmalar',
                                                        'de': 'Bohrungen, Sprengungen, Geologische Arbeiten',
                                                        'zh': '钻探、爆破、地质工程'},
            'Производство полиэтиленовых изделий': {'tr': 'Polietilen Ürün Üretimi',
                                                    'de': 'Herstellung von Polyethylenprodukten', 'zh': '聚乙烯制品生产'},
            'Поставщик стекла': {'tr': 'Cam Tedarikçisi', 'de': 'Glaslieferant', 'zh': '玻璃供应商'},
            'Сотовый оператор': {'tr': 'Cep Telefonu Operatörü', 'de': 'Mobilfunkbetreiber', 'zh': '移动运营商'},
            'Массажный салон': {'tr': 'Masaj Salonu', 'de': 'Massagestudio', 'zh': '按摩沙龙'},
            'Установка Трансформаторов': {'tr': 'Transformatör Kurulumu', 'de': 'Transformatorinstallation',
                                          'zh': '变压器安装'},
            'Культурные центр': {'tr': 'Kültür Merkezi', 'de': 'Kulturzentrum', 'zh': '文化中心'},
            'Туристический тур': {'tr': 'Turistik Tur', 'de': 'Touristische Tour', 'zh': '旅游之旅'},
            'Сварочные работы': {'tr': 'Kaynak İşleri', 'de': 'Schweißarbeiten', 'zh': '焊接工作'},
            'Ремонт компьютеров, оргтехники': {'tr': 'Bilgisayar ve Ofis Teknolojisi Onarımı',
                                               'de': 'Computer- und Bürotechnikreparatur', 'zh': '计算机和办公技术维修'},
            'Игровой клуб': {'tr': 'Oyun Kulübü', 'de': 'Spielclub', 'zh': '游戏俱乐部'},
            'Магазин бытовой химии': {'tr': 'Ev Kimyasalları Mağazası', 'de': 'Haushaltschemikalienladen',
                                      'zh': '家用化学品商店'},
            'Автосалон': {'tr': 'Oto Galeri', 'de': 'Autohaus', 'zh': '汽车展厅'},
            'Авиакомпания': {'tr': 'Havayolu Şirketi', 'de': 'Fluggesellschaft', 'zh': '航空公司'},
            'Авто электрик': {'tr': 'Oto Elektrikçi', 'de': 'Autoelektriker', 'zh': '汽车电工'},
            'Магазин офисных принадлежностей': {'tr': 'Ofis Malzemeleri Mağazası', 'de': 'Bürobedarfsgeschäft',
                                                'zh': '办公用品商店'},
            'Мобильный оператор': {'tr': 'Mobil Operatör', 'de': 'Mobilfunkanbieter', 'zh': '移动运营商'},
            'Кулинарный дом': {'tr': 'Mutfak Evi', 'de': 'Kochhaus', 'zh': '烹饪之家'},
            'Служба доставки': {'tr': 'Teslimat Hizmeti', 'de': 'Lieferdienst', 'zh': '送货服务'},
            'Детектив': {'tr': 'Dedektif', 'de': 'Detektiv', 'zh': '侦探'},
            'DVD Кинотеатр': {'tr': 'DVD Sineması', 'de': 'DVD Kino', 'zh': 'DVD影院'},
            'Кислородная станция': {'tr': 'Oksijen İstasyonu', 'de': 'Sauerstoffstation', 'zh': '氧气站'},
            'Магазин текстиля': {'tr': 'Tekstil Mağazası', 'de': 'Textilgeschäft', 'zh': '纺织品商店'},
            'Обувное производство': {'tr': 'Ayakkabı Üretimi', 'de': 'Schuhproduktion', 'zh': '鞋类制造'},
            'Торговая многопрофильная организация': {'tr': 'Çoklu Ticaret Organizasyonu',
                                                     'de': 'Multifunktionale Handelsorganisation', 'zh': '多业态贸易组织'},
            'Кинозал': {'tr': 'Sinema Salonu', 'de': 'Kinosaal', 'zh': '电影院'},
            'Обучающий курс': {'tr': 'Eğitim Kursu', 'de': 'Lehrkurs', 'zh': '培训课程'},
            'Каталог': {'tr': 'Katalog', 'de': 'Katalog', 'zh': '目录'},
            'Санаторий': {'tr': 'Sanatoryum', 'de': 'Sanatorium', 'zh': '疗养院'},
            'Кризисные центр': {'tr': 'Kriz Merkezi', 'de': 'Krisenzentrum', 'zh': '危机中心'},
            'Магазин штор': {'tr': 'Perde Mağazası', 'de': 'Vorhangladen', 'zh': '窗帘商店'},
            'Половые работы': {'tr': 'Zemin İşleri', 'de': 'Bodenarbeiten', 'zh': '地面工程'},
            'Стартап проект': {'tr': 'Başlangıç Projesi', 'de': 'Start-up-Projekt', 'zh': '初创项目'},
            'Готовые полы': {'tr': 'Hazır Zeminler', 'de': 'Fertigfußböden', 'zh': '成品地板'},
            'Рекламное агентство': {'tr': 'Reklam Ajansı', 'de': 'Werbung Agentur', 'zh': '广告代理'},
            'Телевизионный канал': {'tr': 'Televizyon Kanalı', 'de': 'Fernsehsender', 'zh': '电视频道'},
            'Геодезия и картография': {'tr': 'Jeodezi ve Kartografi', 'de': 'Geodäsie und Kartografie',
                                       'zh': '测绘学和地图制图学'},
            'Биржа': {'tr': 'Borsa', 'de': 'Börse', 'zh': '交易所'},
            'Птицеферма': {'tr': 'Kuş Çiftliği', 'de': 'Vogelfarm', 'zh': '禽兽农场'},
            'Службы ремонта быта': {'tr': 'Ev Tamir Hizmetleri', 'de': 'Haushaltsreparaturdienste', 'zh': '家居维修服务'},
            'Книжный магазин': {'tr': 'Kitapçı', 'de': 'Buchhandlung', 'zh': '书店'},
            'Общества по интересам': {'tr': 'İlgi Grupları', 'de': 'Interessengemeinschaften', 'zh': '兴趣小组'},
            'Частная клиника': {'tr': 'Özel Klinik', 'de': 'Private Klinik', 'zh': '私人诊所'},
            'Диаспора': {'tr': 'Diaspora', 'de': 'Diaspora', 'zh': '侨民'},
            'Курорт': {'tr': 'Tatil Köyü', 'de': 'Kurort', 'zh': '度假村'},
            'Переводческое агентство': {'tr': 'Çeviri Ajansı', 'de': 'Übersetzungsagentur', 'zh': '翻译机构'},
            'Пассажирские ЖД перевозки': {'tr': 'Yolcu Demiryolu Taşımacılığı', 'de': 'Personenbahntransport',
                                          'zh': '旅客铁路运输'},
            'Фирменный магазин': {'tr': 'Marka Mağaza', 'de': 'Markengeschäft', 'zh': '品牌商店'},
            'Лицей': {'tr': 'Lise', 'de': 'Gymnasium', 'zh': '中学'},
            'Озеленительная компания': {'tr': 'Peyzaj Şirketi', 'de': 'Gartenbauunternehmen', 'zh': '绿化公司'},
            'Спортивный магазин': {'tr': 'Spor Mağazası', 'de': 'Sportgeschäft', 'zh': '运动用品商店'},
            'Метавселенная': {'tr': 'Metaevren', 'de': 'Metaversum', 'zh': '元宇宙'},
            'Салон обуви': {'tr': 'Ayakkabı Salonu', 'de': 'Schuhladen', 'zh': '鞋店'},
            'Трудоустройство': {'tr': 'İstihdam', 'de': 'Beschäftigung', 'zh': '就业'},
            'Медицинская оборудование и техника': {'tr': 'Tıbbi Ekipman ve Teknoloji',
                                                   'de': 'Medizinische Ausrüstung und Technik', 'zh': '医疗设备和技术'},
            'Ветеринарные клиника': {'tr': 'Veteriner Kliniği', 'de': 'Tierarztpraxis', 'zh': '兽医诊所'},
            'Установка электро отопительных котлов': {'tr': 'Elektrik Isıtma Kazanı Kurulumu',
                                                      'de': 'Installation von elektrischen Heizkesseln', 'zh': '电暖炉安装'},
            'Прокат товаров': {'tr': 'Eşya Kiralama', 'de': 'Warenverleih', 'zh': '商品租赁'},
            'Социальное учреждение': {'tr': 'Sosyal Kurum', 'de': 'Soziale Einrichtung', 'zh': '社会机构'},
            'Мебель кухня': {'tr': 'Mutfak Mobilyası', 'de': 'Küchenmöbel', 'zh': '厨房家具'},
            'Мясокомбинат': {'tr': 'Et Kombinası', 'de': 'Fleischkombinat', 'zh': '肉类加工厂'}
        }

        for original_name, translations in name_translations.items():
            try:
                items = OrganizationType.objects.filter(title_ru=original_name)

                for item in items:
                    activate('tr')
                    item.title = translations.get('tr', original_name)
                    item.save()

                    activate('de')
                    item.title = translations.get('de', original_name)
                    item.save()

                    activate('zh')
                    item.title = translations.get('zh', original_name)
                    item.save()

                    activate('en')

            except OrganizationCategory.DoesNotExist:
                print(f"OrganizationCategory with name '{original_name}' does not exist.")
                continue

        return Response(data={'message': _('Translations added successfully')}, status=status.HTTP_200_OK)
