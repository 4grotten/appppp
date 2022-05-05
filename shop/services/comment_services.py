from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import CommentsWallpaper
from organizations.models import Membership
from shop.models import Comment, ShopItem
from users.models import User


class CommentService:
    model = Comment

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Comment not found'))

    @classmethod
    def create_comment(cls, text: str, item: ShopItem, user: User, parent: Comment = None, ):
        return cls.model.objects.create(item=item, user=user, parent=parent, text=text)

    @classmethod
    def delete_comment(cls, comment: Comment):
        comment.delete()

    @classmethod
    def get_commented_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, comments__user=user,
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
    def get_wallpapers(cls):
        wallpaper = CommentsWallpaper.objects.filter(is_active=True).first()
        if wallpaper:
            return {'web': 'https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(wallpaper.web_image),
                    'mobile': 'https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(wallpaper.mobile)}
        else:
            return None
