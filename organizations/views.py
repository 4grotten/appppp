from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException
from .models import Organization, OrganizationCategory, DiscountCard
from .serializers import (
    OrganizationListSerializer, OrganizationCreateSerializer, OrganizationDetailedSerializer,
    OrganizationCategorySerializer, OrganizationSerializer,
    OrgPhoneNumberSerializer, OrgPhoneNumberEditSerializer,
    OrgSocialNetworkContactSerializer, OrgSocialNetworkEditSerializer,
    LocationSerializer, DiscountGroupSerializer, DiscountBulkCreateSerializer,
    DiscountCardUpdateSerializer, DiscountCardSerializer,
)
from .services import (
    OrgPhoneNumberService, OrgSocialNetworkContactService,
    OrganizationService, DiscountCardService
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

        organization = serializer.save()

        data = OrganizationDetailedSerializer(organization, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = OrganizationCategorySerializer
    queryset = OrganizationCategory.objects.all()


class OrganizationRetrieveView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer
    queryset = Organization.objects.all()


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

        if organization.owner != request.user:
            raise NotAcceptableException('You can set location')

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


class OrganizationDiscountsAPIView(ListAPIView):
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    serializer_class = DiscountBulkCreateSerializer

    def list(self, request, *args, **kwargs):
        organization_id = request.GET.get('organization', None)

        if organization_id is None:
            return Response(data={
                'message': 'Please provide organization id as a query parameter',
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        discounts = DiscountCardService.get_grouped_discounts(organization_id=organization_id)
        serializer = DiscountGroupSerializer(discounts)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        DiscountCardService.bulk_create_discounts(cards=serializer.validated_data['cards'],
                                                  organization=serializer.validated_data['organization'])

        return Response(data={
            'message': 'Successfully created',
        }, status=status.HTTP_201_CREATED)


class OrganizationDiscountsDeleteUpdateView(UpdateAPIView, DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = DiscountCard.objects.all()
    serializer_class = DiscountCardUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        DiscountCardService.delete_discount(discount_id=kwargs['pk'], user=request.user)
        return Response(data={
            'message': 'Successfully deleted',
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not OrganizationService.user_can_edit_organization(organization_id=instance.organization.id,
                                                              user=request.user):
            raise NotAcceptableException('No rights to edit organization')

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        instance = serializer.save()
        data = DiscountCardSerializer(instance).data
        return Response(data)
