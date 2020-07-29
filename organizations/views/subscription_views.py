from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.categories_serializers import OrganizationWithDiscountsSerializer
from organizations.serializers.misc_serializers import SubscriptionSerializer
from organizations.services.subscription_services import SubscriptionService


class SubscriptionsView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationWithDiscountsSerializer
    filter_backends = (SearchFilter,)
    search_fields = ['title']

    def post(self, request, *args, **kwargs):
        serializer = SubscriptionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        is_subscribed = SubscriptionService.toggle_subscription_status(
            organization=serializer.validated_data['organization'], user=request.user)

        return Response(data={
            'message': 'Successfully updated subscription status',
            'data': {
                'is_subscribed': is_subscribed
            }
        }, status=status.HTTP_200_OK)

    def get_queryset(self):
        return SubscriptionService.get_user_subscriptions(user=self.request.user)
