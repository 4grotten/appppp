from rest_framework import serializers

from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory


class CriteriaSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CriteriaSubcategory
        fields = ('id', 'name',)


class FormatCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatCriteria
        fields = ('id', 'name',)


class SizeFormatSerializer(serializers.ModelSerializer):
    format_criteria = FormatCriteriaSerializer()

    class Meta:
        model = SizeFormat
        fields = ('id', 'size', 'format_criteria',)
