from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.serializers.categories_serializers import OrganizationWithDiscountsSerializer
from organizations.serializers.misc_serializers import SubscriptionSerializer
from organizations.services.subscription_services import SubscriptionService
from users.serializers import UserShortInfoSerializer, FollowerInfoSerializer

User = get_user_model()


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


class OrgFollowersListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserShortInfoSerializer

    def get_queryset(self):
        return SubscriptionService.get_organization_followers(organization_id=self.kwargs['pk'])


class OrgFollowersDetailsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        user = SubscriptionService.get_follower(organization_id=kwargs['organization_id'],
                                                requested_by=self.request.user, user_id=kwargs['user_id'])
        data = FollowerInfoSerializer(user, context={'organization_id': kwargs['organization_id']},
                                      many=False).data
        return Response(data, status=status.HTTP_200_OK)
