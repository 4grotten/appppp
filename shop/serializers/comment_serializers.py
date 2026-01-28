from datetime import timedelta
import re
from channels.db import database_sync_to_async
from django.conf import settings
from rest_framework import serializers

from common.models import File
from organizations.models import Membership, BlockedUser
from organizations.serializers.assistant_serializers import OrganizationAssistantSerializer
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.organization_services import OrganizationService
from messenger_bots.models import BotMessage, BotPlatform
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


class WSParentCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    def get_organization(self, obj):
        user = self.context.get('user')
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization
        if not OrganizationService.user_can_edit_organization(organization, user=user):
            if OrganizationService.user_can_edit_organization(organization, user=obj.user):
                return OrganizationWithTypeImageSerializer(organization).data
        return None

    def get_user(self, obj):
        user = self.context.get('user')
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization
        if not OrganizationService.user_can_edit_organization(organization=organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=organization, user=obj.user):
                return None
            return UserShortInfoSerializer(obj.user).data
        return UserShortInfoSerializer(obj.user).data

    class Meta:
        model = Comment
        fields = ('id', 'user', 'organization', 'text')

class WSCommentSerializer(serializers.ModelSerializer):
    assistant = OrganizationAssistantSerializer()
    is_comment_liked = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    comment_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = WSParentCommentSerializer()
    is_blocked = serializers.SerializerMethodField(default=False, read_only=True)
    is_updated = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    product_data = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    # product_image = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'organization', 'item', 'parent', 'text', 'user_role', 'is_comment_liked', 'is_blocked',
            'comment_like_count', 'can_delete', 'is_updated', 'created_at', 'updated_at', 'assistant', 'source',"product_data","products",'audio'
        ) #'product_image',

    def get_product_data(self, obj):
        """Returns first product found in text (for backwards compatibility)."""
        if not obj.text:
            return None
        match = re.search(r'/p/(\d+)', obj.text)
        if not match:
            return None
        return _get_product_data_by_id(match.group(1))
    

    def get_products(self, obj):
        """
        Returns array of all products found in text.
        Parses all /p/{id} links and returns structured product data.
        """
        if not obj.text:
            return []

        matches = re.findall(r'/p/(\d+)', obj.text)
        if not matches:
            return []

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for item_id in matches:
            if item_id not in seen:
                seen.add(item_id)
                unique_ids.append(item_id)

        products = []
        for item_id in unique_ids:
            product_data = _get_product_data_by_id(item_id)
            if product_data:
                products.append(product_data)

        return products
    # def get_product_image(self, obj):
    #
    #     if not obj.text:
    #         return None
    #     match = re.search(r'/p/(\d+)', obj.text)
    #     if not match:
    #         return None
    #
    #     item_id = match.group(1)
    #
    #     item = ShopItem.objects.filter(id=item_id).first()
    #     if not item:
    #         return None
    #
    #     try:
    #
    #         first_image = item.images.all().order_by('order').first()
    #         if first_image:
    #             if hasattr(first_image, 'medium') and first_image.medium:
    #                 return first_image.medium.url
    #             return first_image.file.url
    #
    #         first_video = item.videos.all().order_by('order').first()
    #         if first_video and first_video.thumbnail:
    #             if hasattr(first_video.thumbnail, 'medium') and first_video.thumbnail.medium:
    #                 return first_video.thumbnail.medium.url
    #             return first_video.thumbnail.file.url
    #
    #     except Exception as e:
    #         print(f"Error getting image for serializer: {e}")
    #         return None
    #
    #     return None

    def get_source(self, obj):
        """Web comments always have source='web'."""
        return 'web'

    def get_is_updated(self, comment: Comment) -> bool:
        return (comment.updated_at - comment.created_at) > timedelta(seconds=1)

    def get_can_delete(self, obj) -> bool:
        user = self.context.get('user')
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization
        return user == obj.user or OrganizationService.user_can_edit_organization(organization, user)

    def get_organization(self, obj):
        user = self.context.get('user')
        organization = obj.item.organization if obj.item else obj.chat.assistant.organization

        if not OrganizationService.user_can_edit_organization(organization, user) and \
                OrganizationService.user_can_edit_organization(organization, obj.user):
            return OrganizationWithTypeImageSerializer(organization).data
        return None

    def get_user(self, obj):
        if obj.user is None:
            return None

        user = self.context.get('user')
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
        user = self.context.get('user')
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
    source = serializers.SerializerMethodField()
    product_data = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'organization', 'item', 'parent', 'text', 'user_role', 'is_comment_liked', 'is_blocked',
            'comment_like_count', 'can_delete', 'is_updated', 'created_at', 'updated_at', 'assistant', 'source',
            'product_data', 'products'
        )

    def get_product_data(self, obj):
        """Returns first product found in text (for backwards compatibility)."""
        if not obj.text:
            return None
        match = re.search(r'/p/(\d+)', obj.text)
        if not match:
            return None
        return _get_product_data_by_id(match.group(1))

    def get_products(self, obj):
        """
        Returns array of all products found in text.
        Parses all /p/{id} links and returns structured product data.
        """
        if not obj.text:
            return []

        matches = re.findall(r'/p/(\d+)', obj.text)
        if not matches:
            return []

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for item_id in matches:
            if item_id not in seen:
                seen.add(item_id)
                unique_ids.append(item_id)

        products = []
        for item_id in unique_ids:
            product_data = _get_product_data_by_id(item_id)
            if product_data:
                products.append(product_data)

        return products

    def get_source(self, obj):
        """Web comments always have source='web'."""
        return 'web'

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


def _get_product_data_by_id(item_id):
    """Helper function to get product data by ID."""
    item = ShopItem.objects.filter(id=item_id).select_related(
        'currency',
        'subcategory',
        'subcategory__category'
    ).prefetch_related(
        'images',
        'videos',
        'videos__thumbnail'
    ).first()

    if not item:
        return None

    try:
        media_urls = []

        for img in item.images.all().order_by('order'):
            if hasattr(img, 'medium') and img.medium:
                media_urls.append(img.medium.url)
            else:
                media_urls.append(img.file.url)

        for vid in item.videos.all().order_by('order'):
            if vid.thumbnail:
                if hasattr(vid.thumbnail, 'medium') and vid.thumbnail.medium:
                    media_urls.append(vid.thumbnail.medium.url)
                else:
                    media_urls.append(vid.thumbnail.file.url)

        return {
            "id": item.id,
            "name": item.name,
            "price": float(item.price) if item.price else None,
            "discount_price": float(item.discounted_price) if item.discounted_price else "",
            "currency": item.currency.code if item.currency else "KGS",
            "description": item.description,
            "category": item.subcategory.category.name if item.subcategory and item.subcategory.category else None,
            "subcategory": item.subcategory.name if item.subcategory else None,
            "images": media_urls,
            "url": f"{settings.SITE_URL}/p/{item.id}"
        }

    except Exception:
        return None


class BotMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for BotMessage (Telegram/WhatsApp messages).
    Returns data in unified format compatible with CommentSerializer.
    """
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    assistant = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    is_comment_liked = serializers.SerializerMethodField()
    comment_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    is_updated = serializers.SerializerMethodField()
    item = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    product_data = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = BotMessage
        fields = (
            'id', 'user', 'organization', 'item', 'parent', 'text', 'user_role',
            'is_comment_liked', 'is_blocked', 'comment_like_count', 'can_delete',
            'is_updated', 'created_at', 'updated_at', 'assistant', 'source', 'product_data', 'products'
        )

    def get_product_data(self, obj):
        """Returns first product found in text (for backwards compatibility)."""
        if not obj.text:
            return None
        match = re.search(r'/p/(\d+)', obj.text)
        if not match:
            return None
        return _get_product_data_by_id(match.group(1))

    def get_products(self, obj):
        """
        Returns array of all products found in text.
        Parses all /p/{id} links and returns structured product data.
        """
        if not obj.text:
            return []

        matches = re.findall(r'/p/(\d+)', obj.text)
        if not matches:
            return []

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for item_id in matches:
            if item_id not in seen:
                seen.add(item_id)
                unique_ids.append(item_id)

        products = []
        for item_id in unique_ids:
            product_data = _get_product_data_by_id(item_id)
            if product_data:
                products.append(product_data)

        return products

    def get_user(self, msg: BotMessage):
        """Return user info for user messages, None for assistant messages."""
        if msg.sender == BotMessage.USER:
            bot_chat = msg.chat
            is_whatsapp = bot_chat.platform == BotPlatform.WHATSAPP
            return {
                'id': bot_chat.id,
                'full_name': bot_chat.user_name or ('WhatsApp User' if is_whatsapp else 'Telegram User'),
                'avatar': {'image': bot_chat.user_photo} if bot_chat.user_photo else None,
                'username': bot_chat.user_phone if is_whatsapp else None,
            }
        return None

    def get_organization(self, msg: BotMessage):
        """Return organization for assistant messages."""
        if msg.sender == BotMessage.ASSISTANT:
            return OrganizationWithTypeImageSerializer(msg.chat.organization).data
        return None

    def get_assistant(self, msg: BotMessage):
        """Return assistant info for assistant messages."""
        if msg.sender == BotMessage.ASSISTANT:
            assistant = getattr(msg.chat.organization, 'assistant', None)
            if assistant:
                return OrganizationAssistantSerializer(assistant).data
        return None

    def get_user_role(self, msg: BotMessage):
        return 'client' if msg.sender == BotMessage.USER else 'assistant'

    def get_is_comment_liked(self, msg: BotMessage):
        return False

    def get_comment_like_count(self, msg: BotMessage):
        return 0

    def get_can_delete(self, msg: BotMessage):
        return False

    def get_parent(self, msg: BotMessage):
        return None

    def get_is_blocked(self, msg: BotMessage):
        return False

    def get_is_updated(self, msg: BotMessage):
        return False

    def get_item(self, msg: BotMessage):
        return None

    def get_source(self, msg: BotMessage):
        """Return source platform: telegram or whatsapp."""
        return msg.chat.platform if msg.chat else None