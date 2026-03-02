from rest_framework import serializers


class OrganizationLinkRequestSerializer(serializers.Serializer):
    organization_id = serializers.IntegerField(min_value=1)
    include_applications = serializers.BooleanField(required=False, default=False)
