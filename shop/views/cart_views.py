from django.db.models import Prefetch, Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from delivery.delivery_services import DeliveryInfoService
from delivery.models import DeliveryInfo
from notifications.constants import NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION, \
    NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT, NOTIFICATION_MODE_SYSTEM
from notifications.models import Notification
from notifications.tasks import send_notifications_to_deliverers, send_delivery_notitication_to_organization_or_client
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from shop.models import Cart, CartItem
from shop.serializers.cart_serializers import (
    CartItemCountChangeSerializer, CartListSerializer, CartSerializer, DeliveryInfoSerializer,
    CartAllItemsCountSerializer, CartUpdateSerializer, EmployeeCartSerializer, DeliveryInfoStatusUpdateSerializer,
)
from shop.services.cart_services import CartItemService, CartService
from transactions.models import Transaction
from transactions.serializers.transaction_serializers import TransactionWithClientSerializer, OffsetUTCSerializer
from transactions.services.transaction_services import TransactionService


class UserCartListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartListSerializer

    def get_queryset(self):
        organization_qs = Organization.objects.all()
        organization_qs = OrganizationService.get_working_time_status(organization_qs, self.request)
        return Cart.objects.filter(user=self.request.user, is_open=True, organization__is_deleted=False). \
            prefetch_related(Prefetch('organization', queryset=organization_qs)).order_by('-id')


class UserCartRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartSerializer

    def get_queryset(self):
        organization_qs = Organization.objects.all()
        organization_qs = OrganizationService.get_working_time_status(organization_qs, self.request)
        return Cart.objects.filter(
            user=self.request.user, is_open=True, organization__is_deleted=False
        ).prefetch_related(Prefetch('items', queryset=CartItem.objects.order_by('-created_at'))). \
            prefetch_related(Prefetch('organization', queryset=organization_qs))

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = EmployeeCartSerializer
        return super().retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        serializer = CartUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        cart = CartService.get_related(id=kwargs['pk'])
        cart = CartService.bulk_update(cart=cart, items=serializer.validated_data['items'], user=self.request.user)
        data = TransactionWithClientSerializer(cart.transaction, context={'request': request}).data
        return Response(data)


class CartItemCountChangeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = CartItemCountChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        size = serializer.validated_data.get('size', None).id \
            if serializer.validated_data.get('size', None) is not None else None
        new_count = CartItemService.change_cart_item_count(
            user=request.user, shop_item=serializer.validated_data['item'],
            change=serializer.validated_data['change'],
            organization=serializer.validated_data.get('organization', None),
            size=size
        )

        data = {
            'item': serializer.validated_data['item'].id,
            'count': new_count,
            'size': size
        }
        return Response(data)


class TotalCartItemsCount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = CartItemService.get_all_items_amount(user=self.request.user)
        data = CartAllItemsCountSerializer({"count": count}).data
        return Response(data, status=status.HTTP_200_OK)


class OrderDeliveryView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = DeliveryInfoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        cart = CartService.process_cart(user=request.user, cart_id=pk, delivery_type=Transaction.CASH_COURIER)
        DeliveryInfoService.create(**serializer.validated_data, transaction=cart.transaction, )

        return Response(
            {
                "message": _("Success"),
                "transaction_id": cart.transaction_id
            }
        )


class OnlinePaymentOrderDeliveryView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = DeliveryInfoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        cart = CartService.process_cart(user=request.user, cart_id=pk, delivery_type=Transaction.ONLINE_PAYMENT)
        DeliveryInfoService.create_for_online_payment(**serializer.validated_data, transaction=cart.transaction, )
        organization = cart.transaction.organization

        if not organization.payment_with_confirmation:
            utc_offset_minutes = int(request.query_params.get('utc_offset_minutes'))
            TransactionService.complete_online_payment_transaction(
                transaction_id=cart.transaction.id,
                utc_offset_minutes=utc_offset_minutes,
                processed_by=organization.owner,
                request=request
            )

        return Response(
            {
                "message": _("Success"),
                "transaction_id": cart.transaction_id
            }
        )


class UpdateDeliveryToSendByCourierView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = DeliveryInfoStatusUpdateSerializer(data=request.data)
        owned_organizations = list(request.user.owned_organizations.all())
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        cart = Cart.objects.get(pk=pk)
        # Fixme check for organization emplees who have access
        # if cart.organization not in owned_organizations:
        #     return Response(data={
        #         'message': _('Invalid input'),
        #         'errors': "Not owner of the organization"
        #     }, status=status.HTTP_403_FORBIDDEN)
        delivery_info = cart.transaction.delivery_info
        if delivery_info.status in (
                DeliveryInfo.DELIVERY_STATUS_DELIVERED,
                DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY
        ):
            return Response(data={
                'message': _('Already delivered'),
                'errors': "Already delivered"
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        delivery_info.who_pays = serializer.initial_data['who_pays']
        delivery_info.status = DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY
        delivery_info.currency = cart.organization.currency
        delivery_info.amount = 200
        # TODO: Find out how to get amount

        delivery_info.save()

        send_delivery_notitication_to_organization_or_client(
            cart.user, cart.id,
            NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT,
            mode=NOTIFICATION_MODE_SYSTEM)
        send_notifications_to_deliverers.delay(
            cart.id,
        )

        pk = cart.organization.pk
        organization = OrganizationService.get(id=pk)
        staff = list(organization.memberships.values_list('user__id', flat=True))
        owner = organization.owner_id
        staff.append(owner)

        Notification.objects.filter(
            extra_data__transaction_id=delivery_info.transaction_id,
            type=NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
            recipient__in=staff
        ).delete()

        return Response(
            {
                "message": _("Success"),
                "transaction_id": cart.transaction_id
            }
        )


class OrderSelfPickupView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        CartService.process_cart(user=request.user, cart_id=pk, delivery_type=Transaction.SELF_PICKUP)
        return Response({'message': _('Success')})


class CartAnonymousCheckoutView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithClientSerializer

    def post(self, request, pk):
        serializer = OffsetUTCSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        transaction = CartService.checkout_cart_for_anonymous_client(
            request=request, employee=request.user, cart_id=pk,
            utc_offset_minutes=serializer.validated_data['utc_offset_minutes']
        )
        data = self.serializer_class(transaction, context={'request': request}).data
        return Response(data)
