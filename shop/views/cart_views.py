from django.db.models import Count
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Cart
from shop.serializers.cart_serializers import CartItemCountChangeSerializer, CartListSerializer
from shop.services.cart_services import CartItemService


class UserCartListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartListSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).annotate(items_count=Count('items')).order_by('-id')


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
            change=serializer.validated_data['change']
        )

        data = {
            'item': serializer.validated_data['item'].id,
            'count': new_count
        }

        return Response(data)
