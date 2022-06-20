import json

from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.models import File
from organizations.models import Organization
from shop.models import ItemCategory, ItemSubcategory, ShopItem
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

        org = Organization.objects.get(title='Белый Кот')
        category = ItemCategory.objects.get(name='House')
        with open('./shop/migrations/myfile.json', 'r') as f:
            data = json.load(f)
        for i in data:
            subcategory, _ = ItemSubcategory.objects.get_or_create(category=category, name=str(i['category']),
                                                                   organization=org)
            images_list = []

            for j in range(len(i['images'])):
                file = File.objects.create(image_url=str(i['images'][j]), is_watermarked=True)
                images_list.append(file)
            item, _ = ShopItem.objects.get_or_create(organization=org, subcategory=subcategory, name=i['name'],
                                                     description=i['description'], price=i['price'],
                                                     youtube_links=i['video'])
            item.images.add(*images_list)

        return StockService.get_sizes_by_format_id(self.kwargs['pk'])
