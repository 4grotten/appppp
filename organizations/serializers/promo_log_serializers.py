from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import PromoEditLog


class PromoEditLogSerializer(serializers.ModelSerializer):
    employee_avatar = ImageSerializer()

    class Meta:
        model = PromoEditLog
        fields = ('id', 'created_at', 'changed_by', 'employee_name', 'employee_role', 'employee_avatar',)
