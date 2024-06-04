from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException, NotAcceptableException
from organizations.models import Assistant, Organization, Answer


class AssistantService:
    model = Assistant

    @classmethod
    def get(cls, *args, **kwargs) -> Assistant:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Assistant not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def exists_for_organization(cls, organization: Organization) -> bool:
        return cls.filter(organization=organization).exists()


class AnswerService:
    model = Answer

    @classmethod
    def get(cls, *args, **kwargs) -> Answer:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Answer not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

