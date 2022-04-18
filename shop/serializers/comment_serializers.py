from rest_framework import serializers

from shop.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('user', 'item', 'parent', 'text')
