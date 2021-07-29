from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException
from common.serializers import CountryCityQueryParamSerializer
from organizations.serializers.organization_serializers import (
    PartnerSerializer, HomepagePartnerSerializer, OrganizationBannerInfo, OrganizationWithTypeImageSerializer
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
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        PartnershipService.create_request(
            user=request.user,
            requested_by=serializer.validated_data['requested_by'],
            accepted_by=serializer.validated_data['accepted_by']
        )

        return Response(data={
            'message': _('Successfully sent partnership request')
        }, status=status.HTTP_200_OK)


class PartnershipRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnershipDetailedSerializer

    def get_queryset(self):
        return PartnershipService.get_incoming_partnerships(partnership_id=self.kwargs['pk'], user=self.request.user)

    def update(self, request, *args, **kwargs):
        serializer = PartnershipUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        partnership = PartnershipService.get(id=self.kwargs['pk'])
        partnership = PartnershipService.set_permissions(partnership=partnership, user=request.user,
                                                         **serializer.validated_data)
        data = PartnershipDetailedSerializer(partnership).data
        return Response(data)

    def destroy(self, request, *args, **kwargs):
        PartnershipService.delete_partnership(partnership_id=self.kwargs['pk'], user=self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationPartnersView(ListAPIView):
    filter_backends = (SearchFilter,)
    search_fields = ('title',)
    serializer_class = PartnerSerializer

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        return OrganizationService.get_organization_partners(organization=organization)


class OrgPartnershipsListView(ListAPIView):
    serializer_class = PartnershipSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('requested_by__title', 'accepted_by__title',)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization_id'] = self.kwargs['pk']
        return context

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        return PartnershipService.get_organization_partnerships(organization=organization, user=self.request.user)


class OrgPartnershipsInShortView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationWithTypeImageSerializer

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        partners = OrganizationService.get_organization_partners(organization=organization)
        return partners


class HomepageRandomPartnersView(ListAPIView):
    serializer_class = HomepagePartnerSerializer

    def get_queryset(self):
        serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid country and city are required in query parameters'))
        country = serializer.validated_data['country']
        city = serializer.validated_data['city']

        return OrganizationService.get_random_organizations_with_min_count_of_partners(country=country, city=city)


class HomepagePartnersListView(ListAPIView):
    serializer_class = PartnerSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('title',)

    def get_queryset(self):
        serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid country and city are required in query parameters'))
        country = serializer.validated_data['country']
        city = serializer.validated_data['city']

        return OrganizationService.get_organizations_ordered_by_num_of_partners(country=country, city=city)


class HomepageBannersView(ListAPIView):
    pagination_class = None
    serializer_class = OrganizationBannerInfo

    def get_queryset(self):
        serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid country and city are required in query parameters'))
        country = serializer.validated_data['country']
        city = serializer.validated_data['city']

        return OrganizationService.get_random_organizations_with_discounts(country=country, city=city)
