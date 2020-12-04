from django.db.models import Q, Case, When, IntegerField
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveUpdateAPIView, RetrieveAPIView, \
    CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, ValidationException
from common.utils import method_permission_classes
from organizations.models import Organization, OrganizationCategory, OrganizationType
from organizations.serializers.categories_serializers import (
    OrganizationCategorySerializer, HomepageOrganizationsSerializer,
    OrganizationWithDiscountsSerializer, OrganizationTypeSerializer
)
from organizations.serializers.misc_serializers import LocationSerializer
from organizations.serializers.organization_serializers import (
    OrganizationListSerializer, OrganizationCreateSerializer, OrganizationDetailedSerializer,
    OrganizationUpdateSerializer, OrgPhoneNumberSerializer, OrgPhoneNumberEditSerializer,
    OrgSocialNetworkContactSerializer, OrgSocialNetworkEditSerializer, OrganizationSerializer, OrgMessageSerializer,
    OrgMessageCreateSerializer, SubscriptionsMessageSerializer, OrganizationWithImageSerializer,
    OrganizationUserTransactionSerializer, InstagramIntegrationCreatUpdateSerializer, OrganizationShortInfoSerializer,
    InstagramIntegrationLinkSerializer
)
from organizations.serializers.query_param_serializers import (
    PartnerQueryParamSerializer, OrganizationAndCategorySerializer
)
from organizations.services.categories_services import OrganizationCategoryService
from organizations.services.organization_services import (
    OrganizationService, OrgPhoneNumberService,
    OrgSocialNetworkContactService, OrgMessageService, OrganizationInstagramIntegrationService
)
from organizations.services.subscription_services import SubscriptionService
from users.serializers import UserShortInfoSerializer


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
                'message': 'Invalid input',
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


class OrganizationRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = OrganizationDetailedSerializer
    queryset = Organization.objects.all()

    @method_permission_classes((IsAuthenticated,))
    def put(self, request, *args, **kwargs):
        serializer = OrganizationUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException('No rights to edit organization')

        updated_organization = OrganizationService.update(organization=organization, **serializer.validated_data)

        return Response(self.serializer_class(updated_organization, context={'request': request}).data)

    @method_permission_classes((IsAuthenticated,))
    def delete(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(user=request.user, organization=organization):
            raise NotAcceptableException('No rights to edit organization')

        deactivated_organization = OrganizationService.deactivate(organization=organization)

        return Response(self.serializer_class(deactivated_organization, context={'request': request}).data)


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
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        numbers = OrgPhoneNumberService.update_phone_numbers(
            organization_id=kwargs['pk'], user=request.user, numbers=serializer.validated_data['phone_numbers'])
        data = OrgPhoneNumberSerializer(numbers, many=True).data
        return Response(data={
            'message': 'Successfully updated',
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
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        networks = OrgSocialNetworkContactService.update_social_networks(
            organization_id=kwargs['pk'], user=request.user, urls=serializer.validated_data['networks'])
        data = OrgSocialNetworkContactSerializer(networks, many=True).data
        return Response(data={
            'message': 'Successfully updated',
            'networks': data
        }, status=status.HTTP_200_OK)


class SetOrganizationLocationAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = LocationSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=pk)

        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise NotAcceptableException('No rights to edit organization')

        changed_organization = OrganizationService.set_location(
            organization=organization,
            longitude=serializer.validated_data.get('longitude'),
            latitude=serializer.validated_data.get('latitude'),
            address=serializer.validated_data.get('address')
        )

        data = OrganizationSerializer(changed_organization, context={'request': request}).data

        return Response(data={
            'message': 'Successfully updated',
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
            raise NotAcceptableException('Valid partner id, country and city are required in query parameters')
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
                'Valid category, partner id, country and city are required in query parameters')

        category = serializer.validated_data['category']
        partner = serializer.validated_data['partner']
        country = serializer.validated_data['country']
        city = serializer.validated_data['city']

        queryset = OrganizationService.get_organizations_in_category(category=category, partner=partner,
                                                                     country=country, city=city)

        return queryset


class HomepageSearchView(ListAPIView):
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('title',)
    filterset_fields = ('country', 'city',)
    serializer_class = OrganizationWithDiscountsSerializer

    def get_queryset(self):
        serializer = PartnerQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise ValidationException('Provide proper partner id')

        partner = serializer.validated_data['partner']
        if partner is None:
            return Organization.objects.filter(is_active=True)

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
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=kwargs['pk'])

        if not OrganizationService.user_can_send_message(organization_id=kwargs['pk'], user=request.user):
            raise PermissionDenied({'message': 'No rights to send message to followers of this organization'})
        OrgMessageService.send_message(organization=organization, content=serializer.validated_data.get('content'),
                                       sender=request.user, message_to=serializer.validated_data.get('message_to'))
        return Response(data={'message': 'Message is created'},
                        status=status.HTTP_201_CREATED)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request

        return context


class OrganizationTitleRetrieveAPIView(RetrieveAPIView):
    serializer_class = OrganizationUserTransactionSerializer
    queryset = OrganizationService.filter()

    def get_serializer_context(self):
        context = super(OrganizationTitleRetrieveAPIView, self).get_serializer_context()
        context['request'] = self.request

        return context


class InstagramIntegrationCreatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': 'No rights to edit organization'})
        data = OrganizationInstagramIntegrationService.get_from_org(organization=organization)
        return Response(
            InstagramIntegrationLinkSerializer(data).data, status=status.HTTP_200_OK)

    def update(self, request, ):
        serializer = InstagramIntegrationCreatUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=kwargs['pk'])

        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': 'No rights to edit organization'})
        OrganizationInstagramIntegrationService.update(organization=organization,
                                                       url=serializer.validated_data.get('url'))
        return Response(data={'message': 'Link added'},
                        status=status.HTTP_201_CREATED)

    def post(self, request, *args, **kwargs):
        serializer = InstagramIntegrationCreatUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(pk=kwargs['pk'])

        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': 'No rights to edit organization'})
        OrganizationInstagramIntegrationService.create(organization=organization,
                                                       url=serializer.validated_data.get('url'))
        return Response(data={'message': 'Link added'},
                        status=status.HTTP_201_CREATED)


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
