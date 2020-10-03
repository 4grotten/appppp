from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem
from shop.serializers.category_serializers import ItemSubcategoryBriefSerializer


class ItemSerializer(serializers.ModelSerializer):
    organization = OrganizationWithTypeImageSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'description',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'youtube_links'
        )


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'description',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'youtube_links'
        )

    def validate(self, attrs):
        user = self.context['request'].user
        organization = attrs['organization']
        subcategory = attrs['subcategory']

        if subcategory.organization is not None and not subcategory.organization == organization:
            raise NotAcceptableException('Organization does not have this subcategory')

        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException('No rights to edit organization')

        return attrs
