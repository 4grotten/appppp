import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Case, When, IntegerField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView, ListAPIView, RetrieveAPIView, GenericAPIView, UpdateAPIView, CreateAPIView
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.utils import method_permission_classes
from mailer.services import MailerService
from organizations.constants import UNDER_REVIEW
from organizations.models import Organization, OrganizationCategory, OrganizationType, InstagramIntegration, Service
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
    OrganizationTitleSerializer, OrgVerificationsSerializer
)
from organizations.serializers.query_param_serializers import (
    PartnerQueryParamSerializer, OrganizationAndCategorySerializer, OrganizationCoutrySerializer
)
from organizations.serializers.service_serializers import OrganizationServiceSerializer
from organizations.services.categories_services import OrganizationCategoryService
from organizations.services.organization_services import (
    OrganizationService, OrgPhoneNumberService, OrgSocialNetworkContactService, OrgMessageService,
    OrganizationInstagramIntegrationService
)
from organizations.services.subscription_services import SubscriptionService
from organizations.services.verifications_service import VerificationService
from organizations.tasks import (
    parse_instagram_to_shop_items
)
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
        data = OrganizationDetailedSerializer(organization, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


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


class OrganizationRetrieveUpdateView(RetrieveAPIView):
    serializer_class = OrganizationDetailedSerializer
    queryset = Organization.objects.all()

    def get_queryset(self):
        queryset = OrganizationService.get_working_time_status(self.queryset, self.request)
        return queryset

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        date_now = datetime.datetime.now()
        if (date_now - instance.add_item_date.replace(tzinfo=None)).seconds > 30 and instance.owner == request.user:
            Organization.objects.filter(id=instance.id).update(add_item_date=date_now)
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

        try:
            service = Service.objects.get(id=self.kwargs['pk'])
        except ObjectDoesNotExist:
            raise ObjectNotFoundException
        queryset = OrganizationService.get_organizations_in_service(service=service,
                                                                    country=country, city=city, request=self.request)
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
        messages = OrgMessageService.get_received_messages(user=self.request.user)
        return messages


class OrgMessageAPIView(ListAPIView):
    serializer_class = OrgMessageSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        messages = OrgMessageService.get_messages_of_organization(organization_id=self.kwargs['pk'])
        return messages

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
            lambda: parse_instagram_to_shop_items.delay(organization_id=organization.id, posts_count=20)
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
