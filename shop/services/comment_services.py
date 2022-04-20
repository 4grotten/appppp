from common.exceptions import ObjectNotFoundException
from django.utils.translation import gettext_lazy as _

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
                                       organization__is_deleted=False).order_by('-comments').distinct()
