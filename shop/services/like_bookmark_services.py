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

        collection.items.set(items)
        return collection

    @classmethod
    def update_collection(cls, collection, name=None, item_id=None, items=None):
        if name is not None:
            collection.name = name
        if item_id is not None:
            item = ShopItem.objects.get(id=item_id)
            collection.image = item
        if items is not None:
            collection.items.remove(*items)
            CollectionService.set_image_to_null_if_collection_has_no_items(collection=collection)
        collection.save()

        return collection

    @classmethod
    def remove_from_all_collections(cls, user: User, item: list, is_bookmarked: bool):
        if not is_bookmarked:
            collections = ItemCollection.objects.filter(user=user)
            for collection in collections:
                collection.items.remove(item)
                CollectionService.set_image_to_null_if_collection_has_no_items(collection=collection)

    @classmethod
    def add_remove_bookmarked_item_collection(cls, user: User, item: ShopItem, is_bookmarked: bool, collection_id: int):
        collection = cls.get(id=collection_id, user=user)
        if is_bookmarked:
            if item in collection.items.all():
                raise NotAcceptableException(_('Item already exists in the collection.'))
            collection.items.add(item)
        else:
            if item not in collection.items.all():
                raise NotAcceptableException(_('Item does not exist in the collection.'))
            collection.items.remove(item)

        CollectionService.set_image_to_null_if_collection_has_no_items(collection=collection)

    @classmethod
    def get_bookmarked_items_in_collection(cls, user: User, collection_id: int):
        collection = ItemCollection.objects.get(id=collection_id, user=user)
        items = collection.items.filter(is_published=True, bookmarked_users__user=user,
                                        organization__is_deleted=False).order_by('-bookmarked_users').distinct()
        return items


    @classmethod
    def set_image_to_null_if_collection_has_no_items(cls, collection: ItemCollection):
        if collection.image is not None and collection.image not in collection.items.all():
            collection.image = None
            collection.save()
