from io import BytesIO

import pandas as pd
from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

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
