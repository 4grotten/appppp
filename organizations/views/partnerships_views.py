from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.organization_serializers import (
    PartnerSerializer, HomepagePartnerSerializer, OrganizationBannerInfo
)
from organizations.serializers.partnership_serializers import (
    PartnershipRequestSerializer, PartnershipSerializer, PartnershipDetailedSerializer, PartnershipUpdateSerializer
)
from organizations.services.organization_services import OrganizationService
from organizations.services.partnership_services import PartnershipService


class PartnershipView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnershipRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        PartnershipService.create_request(
            user=request.user,
            requested_by=serializer.validated_data['requested_by'],
            accepted_by=serializer.validated_data['accepted_by']
        )

        return Response(data={
            'message': 'Successfully sent partnership request'
        }, status=status.HTTP_200_OK)


class PartnershipRetrieveUpdateView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnershipDetailedSerializer

    def get_queryset(self):
        return PartnershipService.get_available_partnerships(partnership_id=self.kwargs['pk'],
                                                             user=self.request.user)

    def update(self, request, *args, **kwargs):
        serializer = PartnershipUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        partnership = self.get_object()
        partnership = PartnershipService.set_permissions(partnership=partnership, **serializer.validated_data)
        data = PartnershipDetailedSerializer(partnership).data
        return Response(data)


class OrganizationPartnersView(ListAPIView):
    filter_backends = (SearchFilter,)
    search_fields = ('title',)
    serializer_class = PartnerSerializer

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        return OrganizationService.get_organization_partners(organization=organization)


class OrgPartnershipsView(ListAPIView):
    serializer_class = PartnershipSerializer

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        return PartnershipService.get_organization_partnerships(organization=organization, user=self.request.user)


class HomepagePartnersView(ListAPIView):
    serializer_class = HomepagePartnerSerializer

    def get_queryset(self):
        return OrganizationService.get_organizations_ordered_by_num_of_partners()


class HomepageBannersView(ListAPIView):
    pagination_class = None
    serializer_class = OrganizationBannerInfo

    def get_queryset(self):
        return OrganizationService.get_random_organizations_with_discounts()
