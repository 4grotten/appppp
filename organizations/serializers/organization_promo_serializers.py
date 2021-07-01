from decimal import Decimal

from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import OrganizationPromo
from organizations.serializers.organization_serializers import OrganizationTitleImageCurrencySerializer
from organizations.serializers.promo_log_serializers import PromoEditLogSerializer


class OrganizationPromoListSerializer(serializers.ModelSerializer):
    organization = OrganizationTitleImageCurrencySerializer()
    image = ImageSerializer()

    class Meta:
        model = OrganizationPromo
        fields = ('id', 'total_cashback', 'cashback', 'image', 'organization',)


class OrganizationPromoDetailedSerializer(OrganizationPromoListSerializer):
    total_cashback = serializers.SerializerMethodField()
    edit_logs = PromoEditLogSerializer(many=True)

    class Meta:
        model = OrganizationPromo
        fields = ('id', 'total_cashback', 'cashback', 'image', 'organization', 'edit_logs',)

    def get_total_cashback(self, promo: OrganizationPromo) -> Decimal:
        return promo.total_cashback - promo.granted_amount


class OrganizationPromoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPromo
        fields = ('organization', 'total_cashback', 'cashback', 'image',)


class OrganizationPromoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPromo
        fields = ('total_cashback', 'cashback', 'image',)
