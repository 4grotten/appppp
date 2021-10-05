from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from delivery.delivery_services import DeliveryInfoService
from delivery.models import DeliveryInfo
from delivery.serializers import DeliveryAllItemsCountSerializer, CartListWithDeliveryInfoSerializer
from notifications.constants import NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE, \
    NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE, \
    NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT, NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT, \
    NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT, \
    NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION, \
    NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION, NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION, \
    NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION
from notifications.models import Notification
from notifications.tasks import send_delivery_notitication_to_organization_or_client


class DeliveryItemsCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = DeliveryInfoService.get_set_for_delivery_count(user=self.request.user)
        data = DeliveryAllItemsCountSerializer({"count": count}).data
        return Response(data, status=status.HTTP_200_OK)


class DeliveryInfoListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartListWithDeliveryInfoSerializer

    def get_queryset(self):
        user = self.request.user
        return DeliveryInfoService.get_available_orders(user)


class AcceptOrderForDeliveryByDeliveryServiceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        delivery_organization = request.user.owned_organizations.filter(
            is_delivery_service=True, is_active=True,
            is_banned=False, is_deleted=False).first()
        if not delivery_organization:
            membership = request.user.memberships.filter(organization__is_delivery_service=True,
                                                         organization__is_active=True,
                                                         organization__is_banned=False,
                                                         organization__is_deleted=False).first()
            if membership:
                delivery_organization = membership.organization
        if not delivery_organization:
            return Response(data={
                'message': _('This user is not delivery service'),
                'errors': _("Not delivery service")
            }, status=status.HTTP_403_FORBIDDEN)
        delivery_info = DeliveryInfo.objects.get(id=kwargs['pk'])
        if delivery_info.status not in (
                DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE,
                DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY):
            return Response(data={
                'message': _('Already taken'),
                'errors': _("Delivery is already taken")
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        delivery_info.status = DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY
        delivery_info.delivery_organization = delivery_organization
        delivery_info.delivery_started = timezone.now()
        delivery_info.save()
        DeliveryInfoService.add_action_history_item(delivery_info, delivery_organization,
                                                    DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY)
        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.client,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT,
            sender_id=delivery_info.transaction.client.id
        )
        # Send notifications to delivery organization and members
        send_delivery_notitication_to_organization_or_client(
            delivery_info.delivery_organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE,
            sender_id=delivery_info.transaction.client.id
        )

        organization_members = list(delivery_info.delivery_organization.memberships.filter(
            Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
        for member in organization_members:
            send_delivery_notitication_to_organization_or_client(
                member.user,
                delivery_info.transaction.cart.id,
                NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE,
                sender_id=delivery_info.transaction.client.id)

        # Send notification to sending organization and its members
        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION,
            sender_id=delivery_info.transaction.delivery_info.delivery_organization.owner.id
        )

        organization_members = list(delivery_info.transaction.organization.memberships.filter(
            Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
        for member in organization_members:
            send_delivery_notitication_to_organization_or_client(
                member.user,
                delivery_info.transaction.cart.id,
                NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION,
                sender_id=delivery_info.transaction.delivery_info.delivery_organization.owner.id
            )

        return Response({'status': 'ok'})


class RejectOrderForDeliveryByDeliveryServiceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        delivery_organizations = list(request.user.owned_organizations.filter(
            is_delivery_service=True, is_active=True,
            is_banned=False, is_deleted=False))

        # if not delivery_organization:
        #     return Response(data={
        #         'message': _('This user is not delivery service'),
        #         'errors': _("Not delivery service")
        #     }, status=status.HTTP_403_FORBIDDEN)

        memberships = list(request.user.memberships.filter(organization__is_delivery_service=True,
                                                           organization__is_active=True,
                                                           organization__is_banned=False,
                                                           organization__is_deleted=False))
        for membership in memberships:
            delivery_organizations.append(membership.organization)

        delivery_info = DeliveryInfo.objects.get(id=kwargs['pk'])
        if delivery_info.delivery_organization not in delivery_organizations:
            return Response(data={
                'message': _('This delivery service is not owner of this delivery'),
                'errors': _("Not your delivery")
            }, status=status.HTTP_401_UNAUTHORIZED)
        if delivery_info.status == DeliveryInfo.DELIVERY_STATUS_DELIVERED:
            return Response(data={
                'message': _('This order is already delivered'),
                'errors': _("Delivered")
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.client,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT,
            sender_id=delivery_info.transaction.client.id
        )

        # Send notifications to delivery organization and members
        send_delivery_notitication_to_organization_or_client(
            delivery_info.delivery_organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE,
            sender_id=delivery_info.transaction.client.id
        )
        organization_members = list(delivery_info.delivery_organization.memberships.filter(
            Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
        for member in organization_members:
            send_delivery_notitication_to_organization_or_client.delay(
                member.user,
                delivery_info.transaction.cart.id,
                NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE,
                sender_id=delivery_info.transaction.client.id
            )

        # Send notification to sending organization and its members
        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION,
            sender_id=delivery_info.transaction.client.id
        )

        organization_members = list(delivery_info.transaction.organization.memberships.filter(
            Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
        for member in organization_members:
            send_delivery_notitication_to_organization_or_client.delay(
                member.user,
                delivery_info.transaction.cart.id,
                NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION,
                sender_id=delivery_info.transaction.client.id
            )


        DeliveryInfoService.add_action_history_item(delivery_info, delivery_info.delivery_organization,
                                                    DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE)

        delivery_info.status = DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY
        delivery_info.delivery_organization = None
        delivery_info.delivery_rejected = timezone.now()
        delivery_info.save()

        return Response({'status': 'ok'})


class DeliveredByDeliveryServiceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        delivery_organizations = list(request.user.owned_organizations.filter(
            is_delivery_service=True, is_active=True,
            is_banned=False, is_deleted=False))

        # if not delivery_organization:
        #     return Response(data={
        #         'message': _('This user is not delivery service'),
        #         'errors': _("Not delivery service")
        #     }, status=status.HTTP_403_FORBIDDEN)

        memberships = list(request.user.memberships.filter(organization__is_delivery_service=True,
                                                     organization__is_active=True,
                                                     organization__is_banned=False,
                                                     organization__is_deleted=False))
        for membership in memberships:
            delivery_organizations.append(membership.organization)

        delivery_info = DeliveryInfo.objects.get(id=kwargs['pk'])
        if delivery_info.delivery_organization not in delivery_organizations:
            return Response(data={
                'message': _('This delivery service is not owner of this delivery'),
                'errors': _("Not your delivery")
            }, status=status.HTTP_401_UNAUTHORIZED)

        if delivery_info.status == DeliveryInfo.DELIVERY_STATUS_DELIVERED:
            return Response(data={
                'message': _('This order is already delivered'),
                'errors': _("Delivered")
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        delivery_info.status = DeliveryInfo.DELIVERY_STATUS_DELIVERED
        delivery_info.delivery_finished = timezone.now()
        delivery_info.save()

        DeliveryInfoService.add_action_history_item(
            delivery_info, delivery_info.delivery_organization,
            DeliveryInfo.DELIVERY_STATUS_DELIVERED)

        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.client,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT)

        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.cart.organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION)

        organization_members = list(delivery_info.transaction.cart.organization.memberships.filter(
            Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
        for member in organization_members:
            send_delivery_notitication_to_organization_or_client(
                member.user,
                delivery_info.transaction.cart.id,
                NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION)

        return Response({'status': 'ok'})


class DeliveryServiceHistoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartListWithDeliveryInfoSerializer

    def get_queryset(self):
        user = self.request.user
        return DeliveryInfoService.get_history_items(user)
