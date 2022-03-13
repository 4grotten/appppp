from rest_framework import serializers

from sms_sender.models import SmsModel


class SmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsModel
        fields = ('id', 'phone_number', 'text', 'status')


class SmsPostSerializer(serializers.Serializer):
    sms_id = serializers.IntegerField()
    sms_status = serializers.ChoiceField(
        choices=['pending', 'success', 'failure'],
    )
    # sms_status = serializers.CharField()
