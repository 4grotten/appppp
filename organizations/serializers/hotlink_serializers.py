from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Hotlink


class HotlinkSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    image = ImageSerializer()

    def get_title(self, hotlink: Hotlink) -> str:
        # ToDo: return item title or organization title according to link_type
        return hotlink.link

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
