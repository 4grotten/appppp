from datetime import timedelta

from rest_framework import serializers

from common.models import File
from organizations.models import Membership, BlockedUser
from organizations.serializers.assistant_serializers import OrganizationAssistantSerializer
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import Comment, CommentLike, CommentComplaint, ShopItem, UserCommentTheme
from shop.services.comment_services import CommentService
from shop.services.like_bookmark_services import LikeService
from users.serializers import UserShortInfoSerializer


class ParentCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    def get_organization(self, obj):
        user = self.context['request'].user
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization
        if not OrganizationService.user_can_edit_organization(organization, user=user):
            if OrganizationService.user_can_edit_organization(organization, user=obj.user):
                return OrganizationWithTypeImageSerializer(organization).data
        return None

    def get_user(self, obj):
        user = self.context['request'].user
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization
        if not OrganizationService.user_can_edit_organization(organization=organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=organization, user=obj.user):
                return None
            return UserShortInfoSerializer(obj.user).data
        return UserShortInfoSerializer(obj.user).data

    class Meta:
        model = Comment
        fields = ('id', 'user', 'organization', 'text')


class CommentSerializer(serializers.ModelSerializer):
    assistant = OrganizationAssistantSerializer()
    is_comment_liked = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    comment_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentCommentSerializer()
    is_blocked = serializers.SerializerMethodField(default=False, read_only=True)
    is_updated = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'organization', 'item', 'parent', 'text', 'user_role', 'is_comment_liked', 'is_blocked',
            'comment_like_count', 'can_delete', 'is_updated', 'created_at', 'updated_at', 'assistant'
        )

    def get_is_updated(self, comment: Comment) -> bool:
        return (comment.updated_at - comment.created_at) > timedelta(seconds=1)

    def get_can_delete(self, obj) -> bool:
        user = self.context['request'].user
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization
        return user == obj.user or OrganizationService.user_can_edit_organization(organization, user)

    def get_organization(self, obj):
        user = self.context['request'].user
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization

        if not OrganizationService.user_can_edit_organization(organization, user) and \
                OrganizationService.user_can_edit_organization(organization, obj.user):
            return OrganizationWithTypeImageSerializer(organization).data
        return None

    def get_user(self, obj):
        if obj.user is None:
            return None

        user = self.context['request'].user
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization

        if not OrganizationService.user_can_edit_organization(organization, user):
            if OrganizationService.user_can_edit_organization(organization, obj.user):
                return None
            return UserShortInfoSerializer(obj.user).data
        return UserShortInfoSerializer(obj.user).data

    def get_user_role(self, obj):
        if obj.chat:
            return CommentService.get_my_role_for_chat(chat=obj.chat, user=obj.user)
        return CommentService.get_my_role(item=obj.item, user=obj.user)

    def get_is_comment_liked(self, comment: Comment) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return LikeService.is_comment_liked_by_user(comment=comment, user=user)

    def get_comment_like_count(self, comment: Comment) -> int:
        return comment.liked_comments.count()

    def get_is_blocked(self, comment: Comment) -> bool:
        organization_id = comment.item.organization.id if comment.item else comment.chat.assistant.organization.id
        blocked_users = BlockedUser.objects.filter(organization_id=organization_id, user=comment.user).values_list(
            'user_id', flat=True).distinct()
        return BlockedUser.objects.filter(user_id__in=blocked_users).exists()


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


class AssistantCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('parent', 'text', 'assistant')


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


class UserCommentThemeSerializer(serializers.ModelSerializer):
    THEME_TYPE_CHOICES = (
        ('default', 'Default'),
        ('predefined', 'Predefined'),
        ('custom', 'Custom'),
    )
    image_id = serializers.IntegerField(required=False, allow_null=True)
    theme_id = serializers.IntegerField(required=False, allow_null=True)
    theme_type = serializers.ChoiceField(choices=THEME_TYPE_CHOICES)

    class Meta:
        model = UserCommentTheme
        fields = ('theme_type', 'image_id', 'theme_id', )