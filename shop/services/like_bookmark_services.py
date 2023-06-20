from common.exceptions import ObjectNotFoundException, NotAcceptableException
from common.models import File
from shop.models import ShopItem, ItemLike, ItemBookmark, Comment, CommentLike, ItemCollection
from users.models import User
from django.utils.translation import gettext_lazy as _


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

    @classmethod
    def like_unlike_comment(cls, user: User, comment: Comment, is_liked: bool):
        if is_liked:
            CommentLike.objects.update_or_create(user=user, comment=comment)
        else:
            CommentLike.objects.filter(user=user, comment=comment).delete()

    @classmethod
    def is_comment_liked_by_user(cls, comment: Comment, user: User) -> bool:
        return CommentLike.objects.filter(user=user, comment=comment).exists()


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


class CollectionService:
    @classmethod
    def get(cls, **filters):
        try:
            return ItemCollection.objects.get(**filters)
        except ItemCollection.DoesNotExist:
            raise ObjectNotFoundException(_('Collection not found'))

    @classmethod
    def filter(cls, **filters):
        return ItemCollection.objects.filter(**filters)

    @classmethod
    def create_collection(cls, name: str, user: User, items: list, image=None):
        collection = ItemCollection.objects.create(
            name=name,
            user=user,
        )
        if items:
            first_item = items[0]
            first_image = first_item.images.first()
            if first_image:
                collection.image = first_image
                collection.save()

        collection.items.set(items)
        return collection

    @classmethod
    def remove_from_all_collections(cls, user: User, item: list, is_bookmarked: bool):
        if not is_bookmarked:
            collections = ItemCollection.objects.filter(user=user)
            for collection in collections:
                collection.items.remove(item)

                if not collection.items.exists():
                    collection.image = None
                    collection.save()

    @classmethod
    def add_remove_bookmarked_item_collection(cls, user: User, item: list, is_bookmarked: bool, collection_id: int):
        collection = cls.get(id=collection_id, user=user)
        if is_bookmarked:
            if item in collection.items.all():
                raise NotAcceptableException(_('Item already exists in the collection.'))
            collection.items.add(item)
        else:
            if item not in collection.items.all():
                return NotAcceptableException(_('Item does not exist in the collection.'))
            collection.items.remove(item)

        if not collection.items.exists():
            collection.image = None
            collection.save()
