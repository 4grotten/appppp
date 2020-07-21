from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers import PartnerSerializer
from organizations.sers.partnership_serializers import PartnershipRequestSerializer
from organizations.services import OrganizationService
from organizations.servs.partnership_services import PartnershipService


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
        return PartnershipService.get_accepted_partners(user=self.request.user, organization=organization)
