import pandas as pd
from io import BytesIO

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from rest_framework import status, filters
from rest_framework.authtoken.models import TokenProxy
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException
from organizations.serializers.categories_serializers import OrganizationWithDiscountsSerializer
from organizations.serializers.misc_serializers import SubscriptionSerializer, AcceptFollowerSerializer
from organizations.services.organization_services import OrganizationService
from organizations.services.partnership_services import PartnershipService
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
            return Response(
                data={
                    'message': _('Invalid input'),
                    'errors': serializer.errors
                }, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        is_subscribed = SubscriptionService.toggle_subscription_status(
            organization=serializer.validated_data['organization'], user=request.user
        )

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
    search_fields = ['full_name', 'username']
    filter_backends = [filters.SearchFilter]

    def get_queryset(self, *args, **kwargs):
        return SubscriptionService.get_organization_followers(organization_id=self.kwargs['pk'], user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user):
            context['can_edit'] = False
        else:
            context['can_edit'] = True
            context['organization'] = organization
        return context


class OrgDownloadFollowersAPIView(APIView):
    # permission_classes = (IsAuthenticated,)

    def get_queryset(self, *args, **kwargs):
        return SubscriptionService.get_organization_followers(organization_id=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        token_key = request.query_params.get('token', request.auth)

        token = TokenProxy.objects.get(key=token_key)
        organization = OrganizationService.get(pk=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=organization, user=token.user):
            return Response({"message": _("Permission denied")}, status=status.HTTP_403_FORBIDDEN)

        queryset = list(self.get_queryset(*args, **kwargs))
        full_names = []
        nicknames = []
        ids = []
        phone_numbers = []
        for item in queryset:
            full_names.append(item.full_name)
            nicknames.append(item.username)
            ids.append(item.id)
            phone_numbers.append(item.phone_number)
        dict_data = {_('Full name'): full_names,
                     _('Nickname'): nicknames,
                     _("ID"): ids,
                     _("Phone number"): phone_numbers}
        df = pd.DataFrame(dict_data)
        with BytesIO() as b:
            # Use the StringIO object as the filehandle.
            writer = pd.ExcelWriter(b, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1', index=False)
            writer.save()
            # Set up the Http response.
            filename = '{title}_followers.xlsx'.format(title=organization.title.replace(" ", ""))
            response = HttpResponse(
                b.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            return response


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


class MassPartnershipSubscriptionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = SubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        organization = serializer.validated_data['organization']
        partner_organizations = PartnershipService.get_organization_partnerships_for_mass_subscription(organization)
        SubscriptionService.subscribe_to_organization(organization, request.user)
        for partner in list(partner_organizations):
            SubscriptionService.subscribe_to_organization(partner.accepted_by, request.user)
            SubscriptionService.subscribe_to_organization(partner.requested_by, request.user)
        return Response(data={
            'message': _('Successfully updated subscription status'),
            'data': {
                'status': 'ok'
            }
        }, status=status.HTTP_200_OK)


class AcceptFollowerView(APIView):
    permission_classes = (IsAuthenticated,)
    serialzier_class = AcceptFollowerSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.serialzier_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        SubscriptionService.accept_follower(organization=serializer.validated_data['organization'],
                                            user=serializer.validated_data['user'])

        if not OrganizationService.user_can_edit_organization(organization=serializer.validated_data['organization'],
                                                              user=self.request.user):
            raise NotAcceptableException(_('No rights to allow follower'))

        return Response(data={
            'message': _('Successfully accept follower'),
            'data': {
                'status': 'ok'
            }
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        serializer = self.serialzier_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        if not OrganizationService.user_can_edit_organization(organization=serializer.validated_data['organization'],
                                                              user=self.request.user):
            raise NotAcceptableException(_('No rights to allow follower'))

        SubscriptionService.refuse_follower(organization=serializer.validated_data['organization'],
                                            user=serializer.validated_data['user'])

        return Response(data={
            'message': _('Refuse follower'),
            'data': {
                'status': 'delete'
            }
        }, status=status.HTTP_204_NO_CONTENT)
