from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Hotlink
from organizations.serializers.organization_serializers import OrganizationWithImageSerializer
from organizations.services.hotlink_services import HotlinkService
from shop.serializers.item_serializers import ItemInHotlinkSerializer


class HotlinkSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    linked_organization = OrganizationWithImageSerializer()
    linked_item = ItemInHotlinkSerializer()
    image = ImageSerializer()

    def get_title(self, hotlink: Hotlink) -> str:
        return HotlinkService.get_hotlink_title(hotlink=hotlink)

    class Meta:
        model = Hotlink
        fields = ('id', 'title', 'link', 'link_type', 'linked_organization', 'linked_item', 'image',)


class HotlinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotlink
        fields = ('organization', 'link', 'image',)


class HotlinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotlink
        fields = ('link', 'image',)
