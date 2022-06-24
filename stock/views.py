import json

from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from stock.models import ShopItemSizeCount
from stock.serializers import FormatCriteriaSerializer, SizeFormatSerializer, CriteriaSubcategorySerializer, \
    CreateStokeCartSerializer, StockCartSerializer, AddSizeQuantitySerializer
from stock.services import StockService


class CriteriaSubcategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CriteriaSubcategorySerializer

    def get_queryset(self):
        return StockService.get_criteria_by_subcategory_id(self.kwargs['pk'])


class FormatCriteriaListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FormatCriteriaSerializer

    def get_queryset(self):
        return StockService.get_format_by_criteria_subcategory_id(self.kwargs['pk'])


class SizeByFormatListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SizeFormatSerializer

    def get_queryset(self):
        return StockService.get_sizes_by_format_id(self.kwargs['pk'])


class CreateStokeCartView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = StockCartSerializer

    def post(self, request, *args, **kwargs):
        serializer = CreateStokeCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        available_size = serializer.validated_data['available_size']
        stock = StockService.create_stock_cart(shop_item_id=self.kwargs['pk'], avaliable_sizes=available_size)
        return Response(self.get_serializer(stock).data)


class SizeQuantityListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddSizeQuantitySerializer

    def get_queryset(self):
        return ShopItemSizeCount.objects.filter(stock_cart_id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        serializer = AddSizeQuantitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        size_format = serializer.validated_data['size_format']
        size_quantity = serializer.validated_data['quantity']
        item_size_count = StockService.add_size_quantity(stock_cart_id=self.kwargs['pk'],
                                                         size_format=size_format,
                                                         quantity=size_quantity)
        return Response(self.get_serializer(item_size_count).data)
