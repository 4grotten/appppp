from urllib.parse import urlparse

from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from common.models import File
from organizations.constants import HOTLINK_PARTNERS, HOTLINK_URL, HOTLINK_COLLECTION
from organizations.models import (
    Hotlink, Organization, HotlinkCollectionSubcategory, HotlinkCollectionItem, HotlinkCollectionLink
)
from organizations.services.organization_services import OrganizationService
from users.models import User


class HotlinkService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Hotlink.objects.get(*args, **kwargs)
        except Hotlink.DoesNotExist:
            raise ObjectNotFoundException(_('Hotlink not found'))

    @classmethod
    def create(cls, *args, **kwargs) -> Hotlink:
        try:
            return Hotlink.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException(_('Could not save hotlink'))

    @classmethod
    def get_hotlinks(cls, organization: Organization):
        return Hotlink.objects.filter(organization=organization).order_by('-updated_at')

    @classmethod
    def get_editable_hotlink_for_user(cls, hotlink_id: int, user: User) -> Hotlink:
        hotlink = cls.get(id=hotlink_id)
        if not OrganizationService.user_can_edit_organization(user=user, organization=hotlink.organization):
            raise ObjectNotFoundException(_('Hotlink not found'))
        if hotlink.link_type == HOTLINK_PARTNERS:
            hotlink.link_type = HOTLINK_URL
        return hotlink

    @classmethod
    @transaction.atomic
    def create_hotlink(cls, user: User, organization: Organization, content: str, link_type: str, image: File,
                       collection_items: list, collection_links: list, collection_subcategories: list):
        if not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        hotlink = cls.create(organization=organization, content=content, link_type=link_type, image=image)

        if link_type == HOTLINK_COLLECTION:
            shop_items_list_to_create = []
            for item in collection_items:
                shop_items_list_to_create.append(HotlinkCollectionItem(hotlink=hotlink, item=item))
            if shop_items_list_to_create:
                HotlinkCollectionItem.objects.bulk_create(shop_items_list_to_create)

            for content in collection_links:
                HotlinkCollectionLink.objects.create(hotlink=hotlink, content=content)

            hotlink_subcategories_to_create = []
            for subcategory in collection_subcategories:
                hotlink_subcategories_to_create.append(
                    HotlinkCollectionSubcategory(hotlink=hotlink, subcategory=subcategory)
                )
            if hotlink_subcategories_to_create:
                HotlinkCollectionSubcategory.objects.bulk_create(hotlink_subcategories_to_create)

    @classmethod
    @transaction.atomic
    def update_hotlink(cls, hotlink: Hotlink, image: File, content: str, link_type: str, collection_items: list,
                       collection_links: list, collection_subcategories: list):
        try:
            hotlink.image = image
            hotlink.content = content
            hotlink.link_type = link_type
            hotlink.save()

            # This part is not the best solution with all the deletion and recreation
            if link_type == HOTLINK_COLLECTION:
                hotlink.collection_items.all().delete()
                shop_items_list_to_create = []
                for item in collection_items:
                    shop_items_list_to_create.append(HotlinkCollectionItem(hotlink=hotlink, item=item))
                if shop_items_list_to_create:
                    HotlinkCollectionItem.objects.bulk_create(shop_items_list_to_create)

                hotlink.collection_links.all().delete()
                for content in collection_links:
                    HotlinkCollectionLink.objects.create(hotlink=hotlink, content=content)

                hotlink.collection_subcategories.all().delete()
                hotlink_subcategories_to_create = []
                for subcategory in collection_subcategories:
                    hotlink_subcategories_to_create.append(
                        HotlinkCollectionSubcategory(hotlink=hotlink, subcategory=subcategory)
                    )
                if hotlink_subcategories_to_create:
                    HotlinkCollectionSubcategory.objects.bulk_create(hotlink_subcategories_to_create)

            return hotlink
        except Exception as e:
            raise IntegrityException(_('Can not update hotlink: {}').format(str(e)))

    @classmethod
    def get_hotlink_title(cls, hotlink: Hotlink) -> str:
        try:
            if hotlink.linked_item is not None:
                return hotlink.linked_item.name
            if hotlink.linked_organization is not None:
                return hotlink.linked_organization.title
        except ObjectNotFoundException:
            pass

        domain = urlparse(hotlink.content).netloc
        if not domain == '':
            return domain

        return hotlink.content

    @classmethod
    def get_hotlink_collection_items(cls, hotlink: Hotlink, user: User) -> QuerySet:
        if not OrganizationService.user_can_edit_organization(organization=hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        from shop.services.item_services import ShopItemService
        items = ShopItemService.get_organization_items_queryset_for_user(organization=hotlink.organization, user=user)
        return items.order_by('-updated_at')

    @classmethod
    def edit_hotlink_selected_items(cls, hotlink: Hotlink, added: list, removed: list, user: User):
        if not OrganizationService.user_can_edit_organization(organization=hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        HotlinkCollectionItem.objects.filter(hotlink=hotlink, item__in=removed).delete()
        existing = HotlinkCollectionItem.objects.filter(hotlink=hotlink, item__in=added
                                                        ).values_list('item_id', flat=True)
        to_create_list = []
        for item in added:
            if item.id not in existing:
                to_create_list.append(HotlinkCollectionItem(hotlink=hotlink, item=item))

        HotlinkCollectionItem.objects.bulk_create(to_create_list)

    @classmethod
    def get_hotlink_collection_subcategories(cls, hotlink: Hotlink, user: User) -> QuerySet:
        if not OrganizationService.user_can_edit_organization(organization=hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        from shop.services.category_services import ItemSubcategoryService
        subcategories = ItemSubcategoryService.get_orgs_nonempty_subcategories(organization_id=hotlink.organization.id)
        return subcategories

    @classmethod
    def edit_hotlink_selected_subcategories(cls, hotlink: Hotlink, added: list, removed: list, user: User):
        if not OrganizationService.user_can_edit_organization(organization=hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        HotlinkCollectionSubcategory.objects.filter(hotlink=hotlink, subcategory__in=removed).delete()
        existing = HotlinkCollectionSubcategory.objects.filter(hotlink=hotlink, subcategory__in=added
                                                               ).values_list('subcategory_id', flat=True)
        to_create_list = []
        for subcategory in added:
            if subcategory.id not in existing:
                to_create_list.append(HotlinkCollectionSubcategory(hotlink=hotlink, subcategory=subcategory))

        HotlinkCollectionSubcategory.objects.bulk_create(to_create_list)


class HotlinkCollectionLinkService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return HotlinkCollectionLink.objects.get(*args, **kwargs)
        except HotlinkCollectionLink.DoesNotExist:
            raise ObjectNotFoundException(_('Hotlink collection link not found'))

    @classmethod
    def create_collection_link(cls, hotlink: Hotlink, content: str, user: User) -> HotlinkCollectionLink:
        if not OrganizationService.user_can_edit_organization(organization=hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))
        return HotlinkCollectionLink.objects.create(hotlink=hotlink, content=content)

    @classmethod
    def get_collection_links(cls, hotlink: Hotlink, user: User) -> QuerySet:
        if not OrganizationService.user_can_edit_organization(organization=hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))
        return HotlinkCollectionLink.objects.filter(hotlink=hotlink).order_by('id')

    @classmethod
    def update_collection_link(cls, collection_link: HotlinkCollectionLink, content: str,
                               user: User) -> HotlinkCollectionLink:
        if not OrganizationService.user_can_edit_organization(
                organization=collection_link.hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))
        collection_link.content = content
        collection_link.save(update_fields=['content'])
        return collection_link

    @classmethod
    def delete_collection_link(cls, collection_link: HotlinkCollectionLink, user: User):
        if not OrganizationService.user_can_edit_organization(
                organization=collection_link.hotlink.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))
        collection_link.delete()
