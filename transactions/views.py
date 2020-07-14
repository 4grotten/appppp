from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers import DiscountCardBriefSerializer
from organizations.services import DiscountCardService
from .serializers import PreprocessQueryParamSerializer
from .services import TransactionService


class TransactionPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = PreprocessQueryParamSerializer(data=dict(request.GET.items()))

        if not serializer.is_valid():
            return Response(data={
                'message': 'Wrong query params',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        client = serializer.validated_data['client']

        transaction = TransactionService.preprocess_transaction(
            client=client, organization=organization, processed_by=request.user
        )
        discount_cards = DiscountCardService.get_available_discounts(
            client=client, organization=organization
        )
        cumulative = None
        if discount_cards['cumulative'] is not None:
            cumulative = DiscountCardBriefSerializer(discount_cards['cumulative']).data

        cards = {
            'cumulative': cumulative,
            'fixed': DiscountCardBriefSerializer(discount_cards['fixed'], many=True).data
        }

        data = {
            'transaction_id': transaction.id,
            'discounts': cards
        }

        return Response(data=data, status=status.HTTP_200_OK)
