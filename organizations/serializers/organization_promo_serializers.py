from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import OrganizationPromo
from organizations.serializers.organization_serializers import OrganizationWithImageSerializer
from organizations.serializers.promo_log_serializers import PromoEditLogSerializer


class OrganizationPromoSerializer(serializers.ModelSerializer):
    organization = OrganizationWithImageSerializer()
    image = ImageSerializer()
    edit_logs = PromoEditLogSerializer(many=True)

    class Meta:
        model = OrganizationPromo
        fields = ('id', 'total_cashback', 'cashback', 'organization', 'image', 'edit_logs',)


class OrganizationPromoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPromo
        fields = ('organization', 'total_cashback', 'cashback', 'image',)


class OrganizationPromoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPromo
        fields = ('total_cashback', 'cashback', 'image',)
