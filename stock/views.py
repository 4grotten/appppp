from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, ListCreateAPIView, GenericAPIView, DestroyAPIView
from io import BytesIO

import pandas as pd
from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from transliterate.utils import _
from rest_framework.views import APIView

from common.exceptions import ObjectNotFoundException
from stock.models import SizeFormat
from stock.models import ShopItemCollections, ShopItemSizeCount
from stock.serializers import FormatCriteriaSerializer, SizeFormatSerializer, CriteriaSubcategorySerializer, \
    CreateStokeCartSerializer, StockCartSerializer, AddSizeQuantitySerializer, CollectionsSerializer, \
    CreateCollectionsSerializer, CreateLinkCollectionsSerializer, ShopItemLinkForCollectionSerializer, \
    LinkCollectionsSerializer
from stock.serializers import FormatCriteriaSerializer, SizeFormatSerializer, CriteriaSubcategorySerializer
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


class CreateShopItemCollections(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CollectionsSerializer

    def get(self, request, *args, **kwargs):
        try:
            collection = ShopItemCollections.objects.get(main_item=self.kwargs['pk'])
        except ShopItemCollections.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))

        return Response(self.get_serializer(collection).data)

    def post(self, request, *args, **kwargs):
        serializer = CreateCollectionsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        related_items = serializer.validated_data['related_items']
        stock = StockService.create_shop_item_collection(main_item=self.kwargs['pk'], related_items=related_items)
        return Response(self.get_serializer(stock).data)


class CreateShopItemLinkCollections(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LinkCollectionsSerializer

    def get(self, request, *args, **kwargs):
        try:
            collection = ShopItemCollections.objects.get(main_item=self.kwargs['pk'])
        except ShopItemCollections.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))

        return Response(self.get_serializer(collection).data)

    def post(self, request, *args, **kwargs):
        serializer = CreateLinkCollectionsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        related_item_links = serializer.validated_data['related_item_links']
        stock = StockService.create_shop_item_collection(main_item=self.kwargs['pk'],
                                                         related_item_links=related_item_links)
        return Response(self.get_serializer(stock).data)


class SizeQuantityListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddSizeQuantitySerializer

    def get_queryset(self):
        return ShopItemSizeCount.objects.filter(stock_cart=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        serializer = AddSizeQuantitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        size_format = serializer.validated_data['size_format']
        size_quantity = serializer.validated_data['quantity']
        item_size_quantity = StockService.add_size_quantity(stock_cart_id=self.kwargs['pk'],
                                                            size_format=size_format,
                                                            quantity=size_quantity)
        return Response(self.get_serializer(item_size_quantity).data)


class AvailableSizeListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SizeFormatSerializer

    def get_queryset(self):
        return SizeFormat.objects.filter(stock_carts=self.kwargs['pk'])


class RemoveShopItemStock(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        StockService.remove_shop_item_stock_cart(stock_id=self.kwargs['pk'])
        return Response(data={
            'message': 'successful remove'
        }, status=status.HTTP_200_OK)


class RemoveShopItemSizeQuantity(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        StockService.remove_shop_item_size_quantity(item_size_quantity_id=self.kwargs['pk'])
        return Response(data={
            'message': 'successful remove',
        }, status=status.HTTP_200_OK)



class DownloadOrgDeliveryInfoAPIView(APIView):
    # permission_classes = (IsAuthenticated,)

    def get_queryset(self, *args, **kwargs):
        return StockService.get_organization_delivery_info(organization_id=self.kwargs['pk'],
                                                           start_time=self.request.query_params.get('start_time'),
                                                           end_time=self.request.query_params.get('end_time'))

    def get(self, request, *args, **kwargs):
        queryset = list(self.get_queryset(*args, **kwargs))

        dict_deals_data = StockService.get_dict_data_for_deals(queryset)
        dict_items_data = StockService.get_dict_data_for_shop_item(queryset)

        df_deals = pd.DataFrame(dict_deals_data)
        df_items = pd.DataFrame(dict_items_data)
        with BytesIO() as b:
            writer = pd.ExcelWriter(b, engine='xlsxwriter')
            df_deals.to_excel(writer, sheet_name='Сделки', index=False)
            df_items.to_excel(writer, sheet_name='Товары', index=False)
            writer.save()
            filename = '{start_time} - {end_time}.xlsx'.format(start_time=self.request.query_params.get('start_time'),
                                                             end_time=self.request.query_params.get('end_time'))
            response = HttpResponse(
                b.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            return response
