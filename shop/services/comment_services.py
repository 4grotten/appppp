import time
import logging
import requests
from django.db import transaction
from django.db.models import Max, Q
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import CommentsWallpaper, File
from common.serializers import ImageSerializer
from instagram_parsers.services.proxy_services import ProxyService
from notifications.constants import NOTIFICATION_MODE_PERSONAL, NEW_COMMENT_TYPE
from notifications.models import Notification
from organizations.models import Membership, Chat, Assistant, Answer
from organizations.services.assistant_services import AssistantService
from shop.models import Comment, ShopItem, UserCommentTheme, CommentTheme
from users.models import User
from notifications.tasks import sent_notification

logger = logging.getLogger(__name__)


class CommentService:
    model = Comment

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Comment not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create_comment(cls, text: str, item: ShopItem, user: User, parent: Comment = None):
        comment = cls.model.objects.create(item=item, user=user, parent=parent, text=text)

        if item.organization.owner != user:
            sent_notification.delay(
                recipient_id=item.organization.owner.id,
                sender_id=user.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NEW_COMMENT_TYPE,
                item_id=item.id,
                organization_id=item.organization.id,
                extra_data=dict(
                    comment_id=comment.id,
                    comment_text=text)
            )

        return comment

    @classmethod
    def create_chat_comment(cls, text: str, chat: Chat, user: User, parent: Comment = None):
        comment = cls.model.objects.create(chat=chat, user=user, parent=parent, text=text)

        return comment

    @classmethod
    def create_chat_assistant_comment(cls, text: str, chat: Chat, assistant: Assistant, parent: Comment = None):
        comment = cls.model.objects.create(chat=chat, assistant=assistant, parent=parent, text=text)

        return comment

    @classmethod
    def create_chat_assistant_default_comment(cls, chat: Chat, assistant: Assistant):
        text = _("Good afternoon! Nice to meet you, how can I help you?")
        comment = cls.model.objects.create(chat=chat, assistant=assistant, text=text)

        return comment

    @classmethod
    def get_training_data(cls, assistant: Assistant):
        answers = Answer.objects.filter(assistant=assistant)
        training_data = {
            "assistant_info": {
                "organization": assistant.organization.title,
                "name": assistant.name,
                "gender": assistant.gender,
                "position": assistant.position,
                "is_enabled": assistant.is_enabled
            },
            "answers": []
        }

        for answer in answers:
            training_data["answers"].append({
                "question": answer.question.text,
                "answer": answer.text,
                "files": [file.file.url for file in answer.files.all()]
            })

        return training_data

    @classmethod
    def create_chat_comment_with_assistant_response(cls, text: str, chat: Chat, user: User, request,
                                                    parent: Comment = None):
        comment = cls.model.objects.create(chat=chat, user=user, parent=parent, text=text)

        host = request.META['HTTP_HOST']

        request_headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "User-Agent": "My User Agent 1.0",
            "Connection": "keep-alive"
        }

        ask_bot_url = 'http://161.35.153.151:8080/bot/'

        data = {
            "assistant_id": chat.assistant.id,
            "parent_id": comment.id,
            "chat_id": chat.id,
            "message": comment.text,
            "host": host,
            "training_data": cls.get_training_data(assistant=chat.assistant)
        }

        sess = requests.Session()
        try:
            response = sess.post(ask_bot_url, json=data, headers=request_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to communicate with AI assistant: {e}")

        return comment

    @classmethod
    def create_chat_comment_with_assistant_default_response(cls, text: str, chat: Chat, user: User,
                                                            parent: Comment = None):
        user_comment = cls.create_chat_comment(chat=chat, user=user, text=text, parent=parent)

        assistant_text = _("Sorry, I'm on vacation!")

        cls.model.objects.create(chat=chat, assistant=chat.assistant, parent=user_comment, text=assistant_text)

        return user_comment

    @classmethod
    def delete_comment(cls, comment: Comment):
        # transaction.on_commit(
        #     lambda: Notification.objects.filter(
        #         Q(extra_data__comment_id=comment.id) & Q(type=NEW_COMMENT_TYPE)
        #     ).delete()
        # )
        comment.delete()

    @classmethod
    def get_income_commented_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, comments__item__organization__owner=user,
                                       organization__is_deleted=False).distinct().annotate(
            comment_date=Max('comments__created_at')).order_by('-comment_date')

    @classmethod
    def get_outcome_commented_items(cls, user: User):
        comments = Comment.objects.filter(user=user)
        return ShopItem.objects.filter(is_published=True, comments__in=comments,
                                       organization__is_deleted=False).distinct().annotate(
            comment_date=Max('comments__created_at')).order_by('-comment_date')

    @classmethod
    def get_my_role(cls, user: User, item: ShopItem):
        try:
            membership = Membership.objects.get(organization=item.organization, user=user)
            return membership.role.title
        except Membership.DoesNotExist:
            if item.organization.owner == user:
                return 'is_owner'
            return None

    @classmethod
    def get_my_role_for_chat(cls, user: User, chat: Chat):
        try:
            membership = Membership.objects.get(organization=chat.assistant.organization, user=user)
            return membership.role.title
        except Membership.DoesNotExist:
            if chat.assistant.organization.owner == user:
                return 'is_owner'
            return None

    @classmethod
    def get_wallpapers(cls):
        wallpaper = CommentsWallpaper.objects.filter(is_active=True).first()
        if wallpaper:
            return {'web': 'https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(wallpaper.web_image),
                    'mobile': 'https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(wallpaper.mobile)}
        else:
            return None

    @classmethod
    def get_user_theme_or_default(cls, user: User):
        user_theme = UserCommentTheme.objects.filter(user=user).first()
        default_theme = CommentTheme.objects.filter(is_active=True).first()

        if user_theme:
            return {
                "theme_type": user_theme.theme_type,
                "theme_id": user_theme.theme_id,
                "image": ImageSerializer(user_theme.image).data if user_theme.image else None,
                "svg_background": default_theme.svg_background.url if default_theme.svg_background else "",
                "svg_pattern": default_theme.svg_pattern.url if default_theme.svg_pattern else ""
            }
        else:

            if default_theme:
                user_theme, created = UserCommentTheme.objects.get_or_create(user=user,
                                                                             defaults={'theme_type': 'default'})
                return {
                    "theme_type": default_theme.theme_type,
                    "theme_id": None,
                    "image": ImageSerializer(user_theme.image).data if user_theme.image else None,
                    "svg_background": default_theme.svg_background.url if default_theme.svg_background else "",
                    "svg_pattern": default_theme.svg_pattern.url if default_theme.svg_pattern else ""
                }
            else:
                return None

    @classmethod
    def update_user_theme(cls, user, theme_type, theme_id=None, image_id=None):
        user_theme, created = UserCommentTheme.objects.get_or_create(user=user)
        user_theme.theme_type = theme_type

        default_theme = CommentTheme.objects.filter(is_active=True).first()

        if theme_type == 'custom' and image_id:
            user_theme.image = File.objects.get(id=image_id)
            user_theme.theme_id = None

        elif theme_type == 'predefined' and theme_id:
            user_theme.theme_id = theme_id

        elif theme_type == 'default':
            if default_theme:
                user_theme.theme_id = None
            else:
                return None

        user_theme.save()

        return {
            "theme_type": user_theme.theme_type,
            "theme_id": user_theme.theme_id,
            "image": ImageSerializer(user_theme.image).data if user_theme.image else None,
            "svg_background": default_theme.svg_background.url if default_theme.svg_background else "",
            "svg_pattern": default_theme.svg_pattern.url if default_theme.svg_pattern else ""
        }

    @classmethod
    def do_read_messages(cls, chat: Chat):
        return cls.filter(is_read=False, chat=chat).update(is_read=True)


