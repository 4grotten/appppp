from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from shop.models import ShopItem
from shop.permissions import CanEditItem
from shop.serializers.item_serializers import ItemCreateUpdateSerializer, ItemSerializer


class ItemCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer


class ItemRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItem)
    serializer_class = ItemCreateUpdateSerializer
    queryset = ShopItem.objects.all()

    def retrieve(self, request, *args, **kwargs):
        self.permission_classes = (AllowAny,)
        self.serializer_class = ItemSerializer
        return super().retrieve(request, *args, **kwargs)
