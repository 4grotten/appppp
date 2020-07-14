from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers import DiscountCardBriefSerializer
from organizations.services import DiscountCardService, CardOwnershipService
from .serializers import PreprocessSerializer
from .services import TransactionService


class TransactionPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PreprocessSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

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

        cumulative = CardOwnershipService.get_client_cumulative_card(client=client, organization=organization)
        fixed = DiscountCardService.get_fixed_discounts_of_organization(organization=organization)

        if cumulative is not None:
            cumulative = DiscountCardBriefSerializer(cumulative).data

        data = {
            'transaction_id': transaction.id,
            'cumulative': cumulative,
            'fixed': DiscountCardBriefSerializer(fixed, many=True).data
        }

        return Response(data=data, status=status.HTTP_200_OK)
