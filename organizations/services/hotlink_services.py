from urllib.parse import urlparse

from django.db import IntegrityError
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from common.models import File
from organizations.models import Hotlink, Organization, HotlinkCollectionSubcategory
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
    def create(cls, *args, **kwargs):
        try:
            Hotlink.objects.create(*args, **kwargs)
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
        return hotlink

    @classmethod
    def create_hotlink(cls, user: User, organization: Organization, content: str, link_type: str, image: File):
        if not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        cls.create(organization=organization, content=content, link_type=link_type, image=image)

    @classmethod
    def update_hotlink(cls, hotlink: Hotlink, image: File, content: str, link_type: str):
        try:
            hotlink.image = image
            hotlink.content = content
            hotlink.link_type = link_type
            hotlink.save()
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
