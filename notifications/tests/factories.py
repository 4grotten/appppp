import factory
import random

from fcm_django.models import FCMDevice

from notifications.constants import NOTIFICATION_TYPES, NOTIFICATION_MODES, SYSTEM_NOTIFICATION_MODE
from notifications.models import NotificationSetting, Notification, NotificationMode
from users.tests.factories import UserFactory

DEVICE_TYPES = ['ios', 'android', 'web']


class NotificationSettingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationSetting


class NotificationModeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationMode


class FCMDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FCMDevice

    registration_id = factory.Sequence(lambda n: f'registration_id{n}')
    type = factory.Sequence(lambda n: DEVICE_TYPES[random.randint(0, 2)])


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    mode, _ = NotificationMode.objects.get_or_create(name=SYSTEM_NOTIFICATION_MODE)
    type = factory.Sequence(lambda n: NOTIFICATION_TYPES[n % 37][1])
    title = factory.Sequence(lambda n: f'Notifications {n}')
    recipient = factory.SubFactory(UserFactory)
    description = factory.Sequence(lambda n: f'Notification Description {n}')
