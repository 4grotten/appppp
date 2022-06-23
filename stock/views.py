import json

from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
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
