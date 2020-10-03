from shop.models import ShopItem, ItemLike, ItemBookmark
from users.models import User


class LikeService:
    @classmethod
    def like_unlike_item(cls, user: User, item: ShopItem, is_liked: bool):
        if is_liked:
            ItemLike.objects.update_or_create(user=user, item=item)
        else:
            ItemLike.objects.filter(user=user, item=item).delete()


class BookmarkService:
    @classmethod
    def add_remove_bookmarked_item(cls, user: User, item: ShopItem, is_bookmarked: bool):
        if is_bookmarked:
            ItemBookmark.objects.update_or_create(user=user, item=item)
        else:
            ItemBookmark.objects.filter(user=user, item=item).delete()
