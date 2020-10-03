from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from shop.serializers.item_serializers import ItemSerializer


class ItemCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemSerializer
