from rest_framework import serializers

from organizations.models import Membership
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import Comment, CommentLike
from shop.services.comment_services import CommentService
from shop.services.like_bookmark_services import LikeService
from users.serializers import UserShortInfoSerializer


class ParentCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=obj.user):
                return OrganizationWithTypeImageSerializer(obj.item.organization).data
            return UserShortInfoSerializer(obj.user).data
        return UserShortInfoSerializer(obj.user).data

    class Meta:
        model = Comment
        fields = ('id', 'user', 'text')


class CommentSerializer(serializers.ModelSerializer):
    is_comment_liked = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    comment_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentCommentSerializer()

    def get_can_delete(self, obj) -> bool:
        user = self.context['request'].user
        if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user) or \
                user == obj.user:
            return True
        return False

    def get_user(self, obj):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=obj.user):
                return OrganizationWithTypeImageSerializer(obj.item.organization).data
            return UserShortInfoSerializer(obj.user).data
        return UserShortInfoSerializer(obj.user).data

    def get_user_role(self, obj):
        return CommentService.get_my_role(item=obj.item, user=obj.user)

    def get_is_comment_liked(self, comment: Comment) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return LikeService.is_comment_liked_by_user(comment=comment, user=user)

    def get_comment_like_count(self, comment: Comment) -> int:
        return comment.liked_comments.count()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'item', 'parent', 'text', 'user_role', 'is_comment_liked', 'comment_like_count', 'can_delete'
            , 'created_at')


class CommentLikeSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()

    class Meta:
        model = CommentLike
        fields = ('comment', 'is_liked')


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('parent', 'text')

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs
