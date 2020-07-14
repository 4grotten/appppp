from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException
from organizations.services import OrganizationService, CardOwnershipService
from .serializers import ClientDiscountInfoSerializer


class ClientDiscountInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = ClientDiscountInfoSerializer(data=dict(request.GET.items()))

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_sell(organization=organization, user=request.user):
            raise NotAcceptableException('No rights to sell in this organization')

        data = CardOwnershipService.get_client_discount_info(
            client=serializer.validated_data['client'],
            organization=organization
        )

        return Response(data=data, status=status.HTTP_200_OK)
