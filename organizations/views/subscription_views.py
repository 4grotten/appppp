from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.serializers.categories_serializers import OrganizationWithDiscountsSerializer
from organizations.serializers.misc_serializers import SubscriptionSerializer
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from users.serializers import FollowerOrClientSerializer, FollowerListSerializer

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
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        is_subscribed = SubscriptionService.toggle_subscription_status(
            organization=serializer.validated_data['organization'], user=request.user)

        return Response(data={
            'message': _('Successfully updated subscription status'),
            'data': {
                'is_subscribed': is_subscribed
            }
        }, status=status.HTTP_200_OK)

    def get_queryset(self):
        return SubscriptionService.get_user_subscriptions(user=self.request.user)


class OrgFollowersListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FollowerListSerializer

    def get_queryset(self):
        return SubscriptionService.get_organization_followers(organization_id=self.kwargs['pk'])

    def get_serializer_context(self):
        context = super().get_serializer_context()

        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user):
            context['can_edit'] = False
        else:
            context['can_edit'] = True
            context['organization'] = organization

        return context


class OrgFollowersDetailsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        user = SubscriptionService.get_follower(organization_id=kwargs['organization_id'],
                                                requested_by=self.request.user, user_id=kwargs['user_id'])
        data = FollowerOrClientSerializer(
            user,
            context={'request': request, 'organization_id': kwargs['organization_id']}
        ).data
        return Response(data, status=status.HTTP_200_OK)
