from rest_framework import serializers
from .models import InstagramApi







class InstagramApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramApi
        fields = ('api_key', 'username')


