from datetime import timedelta

from rest_framework import serializers

from organizations.models import Membership, BlockedUser
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import Comment, CommentLike, CommentComplaint, ShopItem
from shop.services.comment_services import CommentService
from shop.services.like_bookmark_services import LikeService
from users.serializers import UserShortInfoSerializer


class ParentCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    def get_organization(self, obj):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=obj.user):
                return OrganizationWithTypeImageSerializer(obj.item.organization).data
        return None

    def get_user(self, obj):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=obj.user):
                return None
            return UserShortInfoSerializer(obj.user).data
        return UserShortInfoSerializer(obj.user).data

    class Meta:
        model = Comment
        fields = ('id', 'user', 'organization', 'text')


class CommentSerializer(serializers.ModelSerializer):
    is_comment_liked = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    comment_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentCommentSerializer()
    is_blocked = serializers.SerializerMethodField(default=False, read_only=True)
    is_updated = serializers.SerializerMethodField()

    def get_is_updated(self, comment: Comment):
        created_at = comment.created_at
        updated_at = comment.updated_at

        update_threshold = timedelta(seconds=1)
        is_updated = updated_at - created_at > update_threshold
        return is_updated

    def get_can_delete(self, obj) -> bool:
        user = self.context['request'].user
        if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user) or \
                user == obj.user:
            return True
        return False

    def get_organization(self, obj):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=obj.user):
                return OrganizationWithTypeImageSerializer(obj.item.organization).data
        return None

    def get_user(self, obj):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=obj.item.organization, user=obj.user):
                return None
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

    def get_is_blocked(self, comment: Comment) -> bool:
        blocked_users = BlockedUser.objects.filter(organization_id=comment.item.organization.id, user=comment.user).values_list('user_id', flat=True).distinct()
        return BlockedUser.objects.filter(user_id__in=blocked_users).exists()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'organization', 'item', 'parent', 'text', 'user_role', 'is_comment_liked', 'is_blocked',
            'comment_like_count', 'can_delete', 'is_updated', 'created_at', 'updated_at')


class CommentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('text', )


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


class CommentComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentComplaint
        fields = ('comment', 'reason',)

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs


class ItemChangeCommentsDisabledSerializer(serializers.Serializer):
    is_disabled = serializers.BooleanField()
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())
