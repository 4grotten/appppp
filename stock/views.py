from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from stock.serializers import FormatSizeSerializer, ShopItemSizeSerializer
from stock.services import FormatSizeService, ShopItemSizeService


class FormatSizeListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FormatSizeSerializer

    def get_queryset(self):
        return FormatSizeService.get_format_sizes()


class ShopItemSizeByFormatView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopItemSizeSerializer

    def get_queryset(self):
        return ShopItemSizeService.get_sizes_by_format_id(self.kwargs['pk'])
