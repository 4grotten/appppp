from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.misc_serializers import SubscriptionSerializer
from organizations.services.subscription_services import SubscriptionService


class SubscriptionsView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

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