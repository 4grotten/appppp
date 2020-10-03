from common.exceptions import NotAcceptableException
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem
from users.models import User


class ShopItemService:
    @classmethod
    def update_published_status(cls, user: User, item: ShopItem, is_published: bool):
        if not OrganizationService.user_can_edit_organization(user=user, organization=item.organization):
            raise NotAcceptableException('No rights to edit this item')
        item.is_published = is_published
        item.save(update_fields=('is_published',))
