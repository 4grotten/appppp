from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException, NotAcceptableException
from common.models import Currency
from organizations.models import Assistant, Organization, Answer, UserAssistant, Plan
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from users.models import User


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


    @classmethod
    def create_assistant_transaction(cls, user: User, processed_by: User, assistant: Assistant, utc_offset_minutes: int,
                                     plans):
        currency = Currency.objects.get(code='USD')
        total_price = sum(plan.price for plan in plans)

        role = OrganizationService.get_user_role_in_organization(organization=assistant.organization, user=processed_by)

        transaction = Transaction.objects.create(
            client=user,
            processed_by=processed_by,
            employee_role=role,
            employee_name=processed_by.full_name,
            employee_avatar=processed_by.avatar,
            organization=assistant.organization,
            type=Transaction.ASSISTANT,
            delivery_type=Transaction.ONLINE_PAYMENT,
            original_amount=total_price,
            currency=currency,
            status=Transaction.ACCEPTED,
            payment_status=Transaction.IN_PROGRESS,
            display_time=now() + timedelta(minutes=utc_offset_minutes)
        )
        transaction.save()

        return transaction

    @classmethod
    def create_user_assistant(cls, user: User, processed_by: User, assistant: Assistant, plans: Plan,
                              duration_days: int, utc_offset_minutes: int):
        transaction = cls.create_assistant_transaction(user=user, processed_by=processed_by, assistant=assistant,
                                                       plans=plans, utc_offset_minutes=utc_offset_minutes)

        user_assistant = UserAssistant.objects.create(
            user=user,
            assistant=assistant,
            transaction=transaction,
            active_until=timezone.now() + timedelta(days=duration_days)
        )
        user_assistant.plans.set(plans)
        user_assistant.save()

        return user_assistant


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

