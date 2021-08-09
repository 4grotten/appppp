import factory
import random

from fcm_django.models import FCMDevice

from notifications.constants import NOTIFICATION_TYPES, NOTIFICATION_MODES, NOTIFICATION_MODE_SYSTEM
from notifications.models import NotificationSetting, Notification
from users.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory

DEVICE_TYPES = ['ios', 'android', 'web']


class NotificationSettingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationSetting


class FCMDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FCMDevice

    registration_id = factory.Sequence(lambda n: f'registration_id{n}')
    type = factory.Sequence(lambda n: DEVICE_TYPES[random.randint(0, 2)])


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    mode = factory.Sequence(lambda n: NOTIFICATION_MODES[n % len(NOTIFICATION_MODES)][0])
    type = factory.Sequence(lambda n: NOTIFICATION_TYPES[n % len(NOTIFICATION_TYPES)][0])
    title = factory.Sequence(lambda n: f'Notifications {n}')
    recipient = factory.SubFactory(UserFactory)
    description = factory.Sequence(lambda n: f'Notification Description {n}')
    organization = factory.SubFactory(OrganizationFactory)
