from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from stock.serializers import FormatCriteriaSerializer, SizeFormatSerializer
from stock.services import FormatSizeService, SizeFormatService


class FormatCriteriaListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FormatCriteriaSerializer

    def get_queryset(self):
        return FormatSizeService.get_format_of_criteria()


class SizeByFormatView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SizeFormatSerializer

    def get_queryset(self):
        return SizeFormatService.get_sizes_by_format_id(self.kwargs['pk'])
