from rest_framework import serializers

from common.exceptions import NotAcceptableException
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'organization', 'subcategory',
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
