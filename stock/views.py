from django.db.models import Q
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListCreateAPIView, DestroyAPIView, RetrieveAPIView
from io import BytesIO

import pandas as pd
from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from shop.models import ShopItem
from shop.services.item_services import ShopItemService
from stock.models import SizeFormat, ShopItemSetStock, ShopItemLinksSetStock, ShopItemSizeCount
from stock.serializers import FormatCriteriaSerializer, SizeFormatSerializer, CriteriaSubcategorySerializer, \
    CreateAvailableSizesSerializer, ShopItemsAvailableSizesSerializer, ShopItemsSetSerializer, ShopItemShortSerializer, \
    LinkStockSerializer, ShopItemSetSerializer, ShopItemLinkSetSerializer, ShopItemSizeCountSetSerializer, \
    AddShopItemSizeCountSetSerializer, StockSerializer, StockSetsSerializer, ShopLinkItemsSetSerializer
from stock.services import StockService


class StockView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = StockSerializer

    def get_object(self):
        return ShopItem.objects.get(id=self.kwargs['pk'])


class StockSetsView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = StockSetsSerializer

    def get_object(self):
        return ShopItem.objects.get(id=self.kwargs['pk'])


class StockSetItemsView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopItemSetSerializer

    def get_queryset(self):
        try:
            main_shop_item = ShopItem.objects.get(id=self.kwargs['pk'])
            return ShopItem.objects.filter(
                Q(shop_items_set_stocks__main_shop_item=main_shop_item) |
                Q(shop_items_link_set_stocks__main_shop_item=main_shop_item)
            )
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))


class CriteriaSubcategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CriteriaSubcategorySerializer
    pagination_class = None

    def get_queryset(self):
        return StockService.get_criteria_by_subcategory_id(self.kwargs['pk'])


class FormatCriteriaListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FormatCriteriaSerializer
    pagination_class = None

    def get_queryset(self):
        return StockService.get_format_by_criteria_subcategory_id(self.kwargs['pk'])


class SizeByFormatListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SizeFormatSerializer
    pagination_class = None

    def get_queryset(self):
        return StockService.get_sizes_by_format_id(self.kwargs['pk'])


class AvailableSizeListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SizeFormatSerializer
    pagination_class = None

    def get_queryset(self):
        return SizeFormat.objects.filter(shop_items=self.kwargs['pk'])

    def create(self, request, *args, **kwargs):
        serializer = CreateAvailableSizesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        available_sizes = serializer.validated_data['available_sizes']
        shop_item = StockService.add_available_sizes(shop_item_id=self.kwargs['pk'], available_sizes=available_sizes)
        available_sizes_serializer = ShopItemsAvailableSizesSerializer(shop_item).data
        return Response(available_sizes_serializer)


class ShopItemsSetCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopItemsSetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        shop_items_set = serializer.validated_data['shop_items_set']
        StockService.add_shop_items_sets(main_item=self.kwargs['pk'], shop_items=shop_items_set)
        return Response(data={
            'message': _('Successfully add set.')
        }, status=status.HTTP_200_OK)


class ShopLinkItemsSetCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopLinkItemsSetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        shop_items_link_set = serializer.validated_data['shop_items_link_set']
        StockService.add_shop_link_items_sets(main_item=self.kwargs['pk'], shop_item_links=shop_items_link_set)
        return Response(data={
            'message': _('Successfully add set.')
        }, status=status.HTTP_200_OK)


class GetShopItemByLink(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopItemShortSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        serializer = LinkStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        shop_item = StockService.get_shop_item_by_link(link=serializer.validated_data['link'])
        return Response(self.serializer_class(shop_item).data)


class ShopItemSetListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopItemSetSerializer

    def get_queryset(self):
        try:
            shop_item_stock = ShopItemSetStock.objects.get(main_shop_item=self.kwargs['pk'])
            return shop_item_stock.shop_item.all()
        except ShopItemSetStock.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItemSetStock not found'))


class ShopItemLinkSetListView(ListAPIView):
    serializer_class = ShopItemLinkSetSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        item = ShopItem.objects.get(id=self.kwargs['pk'])
        return ShopItem.objects.filter(shop_items_link_set_stocks__main_shop_item=item)


class GetNotChoosenSizeListView(ListAPIView):
    serializer_class = SizeFormatSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        return StockService.get_not_choosen_size(main_item=self.kwargs['pk'])


class ShopItemSizeCountView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopItemSizeCountSetSerializer
    pagination_class = None

    def get_queryset(self):
        return ShopItemSizeCount.objects.filter(main_shop_item=self.kwargs['pk'])

    def create(self, request, *args, **kwargs):
        serializer = AddShopItemSizeCountSetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        size = serializer.validated_data['size']
        count = serializer.validated_data['count']
        size_count = StockService.add_shop_items_size_count(main_item=self.kwargs['pk'], size=size,
                                                            count=count)
        return Response(self.serializer_class(size_count).data)


class DeleteStockView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        shop_item = ShopItemService.get(id=kwargs['pk'])
        ShopItemSizeCount.objects.filter(main_shop_item=shop_item).delete()
        ShopItemSetStock.objects.filter(main_shop_item=shop_item).delete()
        ShopItemLinksSetStock.objects.filter(main_shop_item=shop_item).delete()

        shop_item.available_sizes.clear()

        return Response(data={
            'message': _('Successfully deleted'),
        }, status=status.HTTP_200_OK)


class DeleteShopItemSizeCountView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        ShopItemSizeCount.objects.get(id=self.kwargs['pk']).delete()

        return Response(data={
            'message': _('Successfully deleted'),
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
            if self.request.query_params.get('start_time') and self.request.query_params.get('end_time'):
                filename = '{start_time} - {end_time}.xlsx'.format(start_time=self.request.query_params.get('start_time'),
                                                                   end_time=self.request.query_params.get('end_time'))
                if self.request.query_params.get('start_time') == self.request.query_params.get('end_time'):
                    filename = f'{self.request.query_params.get("start_time")}.xlsx'
            else:
                start_date, end_date = StockService.get_organization_delivery_min_and_max_date_info(organization_id=self.kwargs['pk'])
                filename = f'{start_date} - {end_date} (all time report).xlsx'
            response = HttpResponse(
                b.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            return response
