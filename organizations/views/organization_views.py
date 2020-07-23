from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException
from organizations.models import Organization, OrganizationCategory
from organizations.serializers.categories_serializers import (
    OrganizationCategorySerializer, HomepageOrganizationsSerializer
)
from organizations.serializers.misc_serializers import LocationSerializer
from organizations.serializers.organization_serializers import (
    OrganizationListSerializer, OrganizationCreateSerializer,
    OrganizationDetailedSerializer, OrganizationUpdateSerializer,
    OrgPhoneNumberSerializer, OrgPhoneNumberEditSerializer, OrgSocialNetworkContactSerializer,
    OrgSocialNetworkEditSerializer, OrganizationSerializer
)
from organizations.services.categories_services import OrganizationCategoryService
from organizations.services.organization_services import (
    OrganizationService, OrgPhoneNumberService, OrgSocialNetworkContactService
)


class OrganizationsListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(Q(owner=user) | Q(memberships__user=user))

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


class OrganizationRetrieveView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer
    queryset = Organization.objects.all()

    def put(self, request, *args, **kwargs):
        serializer = OrganizationUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        if not OrganizationService.user_can_edit_organization(user=request.user, organization_id=kwargs['pk']):
            raise NotAcceptableException('No rights to edit organization')

        organization = OrganizationService.get(pk=kwargs['pk'])

        updated_organization = OrganizationService.update(organization=organization, **serializer.validated_data)

        return Response(self.serializer_class(updated_organization, context={'request': request}).data)

    def delete(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs['pk'])

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

        if not OrganizationService.user_can_edit_organization(organization_id=pk, user=request.user):
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

    def get_queryset(self):
        return OrganizationCategoryService.get_nonempty_categories()
