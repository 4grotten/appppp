from urllib.parse import urlparse

from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from common.models import File
from organizations.constants import HOTLINK_ITEM, HOTLINK_ORGANIZATION
from organizations.models import Hotlink, Organization
from organizations.services.organization_services import OrganizationService
from shop.services.item_services import ShopItemService
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
    def create_hotlink(cls, user: User, organization: Organization, link: str, image: File):
        if not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        # ToDo: parse link and set link_type accordingly
        cls.create(organization=organization, link=link, image=image)

    @classmethod
    def update_hotlink(cls, hotlink: Hotlink, image: File, link: str):
        try:
            hotlink.image = image
            hotlink.link = link
            hotlink.save()
            return hotlink
        except Exception as e:
            raise IntegrityException(_('Can not update hotlink: {}').format(str(e)))

    @classmethod
    def get_hotlink_title(cls, hotlink: Hotlink) -> str:
        try:
            if hotlink.link_type == HOTLINK_ITEM:
                item = ShopItemService.get(id=int(hotlink.linked_item_id))
                return item.name
            if hotlink.link_type == HOTLINK_ORGANIZATION:
                organization = OrganizationService.get(id=hotlink.linked_item_id)
                return organization.title
        except ObjectNotFoundException:
            return urlparse(hotlink.link).netloc

        return urlparse(hotlink.link).netloc
