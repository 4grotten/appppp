from django.db.models import Prefetch
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Cart, CartItem
from shop.serializers.cart_serializers import (
    CartItemCountChangeSerializer, CartListSerializer, CartSerializer, DeliveryInfoSerializer,
    CartAllItemsCountSerializer, CartUpdateSerializer, EmployeeCartSerializer,
)
from shop.services.cart_services import CartItemService, CartService, DeliveryInfoService
from transactions.models import Transaction
from transactions.serializers.transaction_serializers import TransactionWithClientSerializer, OffsetUTCSerializer


class UserCartListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartListSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user, is_open=True, organization__is_deleted=False).order_by('-id')


class UserCartRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(
            user=self.request.user, is_open=True, organization__is_deleted=False
        ).prefetch_related(Prefetch('items', queryset=CartItem.objects.order_by('-created_at')))

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = EmployeeCartSerializer
        return super().retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        serializer = CartUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
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
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        new_count = CartItemService.change_cart_item_count(
            user=request.user, shop_item=serializer.validated_data['item'],
            change=serializer.validated_data['change'],
            organization=serializer.validated_data.get('organization', None),
        )

        data = {
            'item': serializer.validated_data['item'].id,
            'count': new_count
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
        serializer = DeliveryInfoSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        cart = CartService.close_the_cart(user=request.user, cart_id=pk, delivery_type=Transaction.CASH_COURIER)
        DeliveryInfoService.create(**serializer.validated_data, user=request.user, transaction=cart.transaction, )
        return Response(
            {
                "message": "Success",
                "transaction_id": cart.transaction_id
            }
        )


class OrderSelfPickupView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        CartService.close_the_cart(user=request.user, cart_id=pk, delivery_type=Transaction.SELF_PICKUP)
        return Response({'message': 'Success'})


class CartAnonymousCheckoutView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithClientSerializer

    def post(self, request, pk):
        serializer = OffsetUTCSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        transaction = CartService.checkout_cart_for_anonymous_client(
            request=request, employee=request.user, cart_id=pk,
            utc_offset_minutes=serializer.validated_data['utc_offset_minutes']
        )
        data = self.serializer_class(transaction, context={'request': request}).data
        return Response(data)
