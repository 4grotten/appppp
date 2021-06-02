from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Hotlink
from organizations.services.hotlink_services import HotlinkService


class HotlinkSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    image = ImageSerializer()

    def get_title(self, hotlink: Hotlink) -> str:
        return HotlinkService.get_hotlink_title(hotlink=hotlink)

    class Meta:
        model = Hotlink
        fields = ('id', 'title', 'link', 'link_type', 'image',)


class HotlinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotlink
        fields = ('organization', 'link', 'image',)


class HotlinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotlink
        fields = ('link', 'image',)
