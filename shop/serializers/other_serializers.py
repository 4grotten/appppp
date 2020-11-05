from rest_framework import serializers

from shop.models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ('item', 'reason',)

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs
