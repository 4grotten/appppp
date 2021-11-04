from django.db.models import Value,ExpressionWrapper, CharField
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import MessageText
from organizations.services.organization_services import OrganizationService


class ShadowService:
    model = MessageText

    @classmethod
    def get_status(cls, pk) -> str:
        organization = OrganizationService.get(pk=pk)
        is_under_review = organization.is_under_review
        return is_under_review

    @classmethod
    def get_message(cls, message_type: str, status: str) -> MessageText:
        message = cls.model.objects.filter(message_type=message_type).\
            annotate(is_under_review=ExpressionWrapper(Value(status), output_field=CharField())).last()
        if message:
            return message
        raise ObjectNotFoundException(_('Message not found'))
