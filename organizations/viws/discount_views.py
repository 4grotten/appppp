from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.sers.bulk_serializers import BulkDeleteSerializer, BulkUpdateSerializer
from organizations.services import DiscountCardService


class DiscountsBulkUpdateView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BulkUpdateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        # if not serializer.is_valid():
        #     return Response(data={
        #         'message': 'Invalid input',
        #         'errors': serializer.errors
        #     }, status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response(data={
            'message': 'Successfully updated cards',

        }, status=status.HTTP_200_OK)


class DiscountsBulkDeleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BulkDeleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        DiscountCardService.bulk_delete_discounts(cards=serializer.validated_data['cards'],
                                                  organization=serializer.validated_data['organization'],
                                                  deleted_by=request.user)

        return Response(data={
            'message': 'Successfully deleted cards',

        }, status=status.HTTP_200_OK)
