from shop.models import ShopItem, ItemLike, ItemBookmark
from users.models import User


class LikeService:
    @classmethod
    def like_unlike_item(cls, user: User, item: ShopItem, is_liked: bool):
        if is_liked:
            ItemLike.objects.update_or_create(user=user, item=item)
        else:
            ItemLike.objects.filter(user=user, item=item).delete()

    @classmethod
    def is_item_liked_by_user(cls, item: ShopItem, user: User) -> bool:
        return ItemLike.objects.filter(user=user, item=item).exists()


class BookmarkService:
    @classmethod
    def add_remove_bookmarked_item(cls, user: User, item: ShopItem, is_bookmarked: bool):
        if is_bookmarked:
            ItemBookmark.objects.update_or_create(user=user, item=item)
        else:
            ItemBookmark.objects.filter(user=user, item=item).delete()

    @classmethod
    def is_item_bookmarked_by_user(cls, item: ShopItem, user: User) -> bool:
        return ItemBookmark.objects.filter(user=user, item=item).exists()
