from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.organization_serializers import (
    PartnerSerializer, HomepagePartnerSerializer, OrganizationBannerInfo
)
from organizations.serializers.partnership_serializers import PartnershipRequestSerializer
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


class OrganizationPartnersView(ListAPIView):
    serializer_class = PartnerSerializer

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        return OrganizationService.get_organization_partners(organization=organization)


class HomepagePartnersView(ListAPIView):
    serializer_class = HomepagePartnerSerializer

    def get_queryset(self):
        return OrganizationService.get_organizations_ordered_by_num_of_partners()


class HomepageBannersView(ListAPIView):
    pagination_class = None
    serializer_class = OrganizationBannerInfo

    def get_queryset(self):
        return OrganizationService.get_latest_created_organizations_with_discounts()
