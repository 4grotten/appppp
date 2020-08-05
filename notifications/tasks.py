from celery import shared_task
from django.contrib.auth import get_user_model

from notifications.constants import SUBSCRIPTION_NOTIFICATION_MODE, NEW_ORGANIZATION, NEW_ORGANIZATION_TITLE
from notifications.services import NotificationService
from organizations.models import Organization

User = get_user_model()


@shared_task
def send_notifications_to_all_users(organization: Organization, user: User):
    users = User.objects.exclude(id=user.id)

    for user in users:
        NotificationService.create_notification(
            recipient=user,
            mode=SUBSCRIPTION_NOTIFICATION_MODE,
            notification_type=NEW_ORGANIZATION,
            title=NEW_ORGANIZATION_TITLE,
            description=organization.address,
            organization=organization
        )
