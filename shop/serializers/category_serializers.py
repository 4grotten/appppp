from django.db.models import Q
from rest_framework import serializers

from shop.models import MainCategory, ItemCategory


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ('id', 'name', 'organization',)


class MainCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    def get_subcategories(self, main_category: MainCategory) -> dict:
        organization = self.context['organization']
        if organization is None:
            subcategories = main_category.subcategories.filter(organization__isnull=True)
        else:
            subcategories = main_category.subcategories.filter(
                Q(organization__isnull=True) | Q(organization=organization))
        return ItemCategorySerializer(subcategories, many=True).data

    class Meta:
        model = MainCategory
        fields = ('id', 'name', 'subcategories')
