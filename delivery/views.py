from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from delivery.delivery_services import DeliveryInfoService
from delivery.models import DeliveryInfo
from delivery.serializers import DeliveryAllItemsCountSerializer, CartListWithDeliveryInfoSerializer
from notifications.constants import NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT, \
    NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE, NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE, \
    NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT, NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT
from notifications.tasks import send_delivery_notitication_to_organization_or_client


class DeliveryItemsCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = DeliveryInfoService.get_all_items_count(user=self.request.user)
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
        delivery_organization = request.user.owned_organizations.filter(is_delivery_service=True, is_active=True,
                                                                        is_banned=False, is_deleted=False).first()
        if not delivery_organization:
            return Response(data={
                'message': _('This user is not delivery service'),
                'errors': _("Not delivery service")
            }, status=status.HTTP_403_FORBIDDEN)
        delivery_info = DeliveryInfo.objects.get(id=kwargs['pk'])
        if delivery_info.status not in (
        DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE, DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY):
            return Response(data={
                'message': _('Already taken'),
                'errors': _("Delivery is already taken")
            }, status=status.HTTP_406_NOT_ACCEPTABLE)


        delivery_info.status = DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY
        delivery_info.delivery_organization = delivery_organization
        delivery_info.save()
        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.client,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT)
        send_delivery_notitication_to_organization_or_client(
            delivery_info.delivery_organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE)
        return Response({'status': 'ok'})


class RejectOrderForDeliveryByDeliveryServiceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        delivery_organization = request.user.owned_organizations.filter(is_delivery_service=True, is_active=True,
                                                                        is_banned=False, is_deleted=False).first()

        if not delivery_organization:
            return Response(data={
                'message': _('This user is not delivery service'),
                'errors': _("Not delivery service")
            }, status=status.HTTP_403_FORBIDDEN)
        delivery_info = DeliveryInfo.objects.get(id=kwargs['pk'])
        if delivery_info.delivery_organization != delivery_organization:
            return Response(data={
                'message': _('This delivery service is not owner of this delivery'),
                'errors': _("Not your delivery")
            }, status=status.HTTP_401_UNAUTHORIZED)
        if delivery_info.status == DeliveryInfo.DELIVERY_STATUS_DELIVERED:
            return Response(data={
                'message': _('This order is already delivered'),
                'errors': _("Delivered")
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        delivery_info.status = DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE
        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.client,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT)
        send_delivery_notitication_to_organization_or_client(
            delivery_info.delivery_organization.owner,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE)
        delivery_info.save()

        return Response({'status': 'ok'})


class DeliveredByDeliveryServiceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        delivery_organization = request.user.owned_organizations.filter(is_delivery_service=True, is_active=True,
                                                                        is_banned=False, is_deleted=False).first()
        if not delivery_organization:
            return Response(data={
                'message': _('This user is not delivery service'),
                'errors': _("Not delivery service")
            }, status=status.HTTP_403_FORBIDDEN)
        delivery_info = DeliveryInfo.objects.get(id=kwargs['pk'])
        if delivery_info.delivery_organization != delivery_organization:
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
        delivery_info.save()
        send_delivery_notitication_to_organization_or_client(
            delivery_info.transaction.client,
            delivery_info.transaction.cart.id,
            NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT)
        return Response({'status': 'ok'})


class DeliveryServiceHistoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartListWithDeliveryInfoSerializer

    def get_queryset(self):
        user = self.request.user
        return DeliveryInfoService.get_history_items(user)