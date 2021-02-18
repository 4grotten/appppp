from django.test import TestCase
from notifications.models import Notification, NotificationMode
from unittest.mock import patch, Mock, call

from notifications.tests.factories import NotificationSettingFactory, NotificationFactory, NotificationModeFactory, \
    FCMDeviceFactory
from users.tests.factories import UserFactory


class NotificationSendMessageTest(TestCase):
    def setUp(self):
        self.user = UserFactory(phone_number='+996555422121')
        self.notification_settings = NotificationSettingFactory(user=self.user)
        self.notification = NotificationFactory()
        self.notification_android_device = FCMDeviceFactory(type='android')
        self.notification_ios_device = FCMDeviceFactory(type='ios')
        self.notification_web_device = FCMDeviceFactory(type='web')

        self.notification_settings.fcm_device.add(self.notification_android_device, self.notification_ios_device,
                                                  self.notification_web_device)

    @patch('fcm_django.models.FCMDeviceQuerySet.send_message')
    def test_passed_send_notification(self, mocked_send_message: Mock):
        Notification.send_notification(user=self.user, title=self.notification.title,
                                       title_ru=self.notification.title_ru,
                                       description=self.notification.description,
                                       description_ru=self.notification.description_ru,
                                       mode=self.notification.mode.name,
                                       notification_id=self.notification.id,
                                       organization=self.notification.organization,
                                       type=self.notification.type,
                                       extra_data=self.notification.extra_data)
        self.assertEqual(mocked_send_message.call_count, 4)

    @patch('fcm_django.models.FCMDeviceQuerySet.send_message')
    def test_do_not_sent_because_of_settings_send_notification(self, mocked_send_message: Mock):
        user = UserFactory(phone_number='+996555422122')
        notification_settings = NotificationSettingFactory(user=user, organization_notifications=False)
        notification = NotificationFactory(mode=NotificationMode.objects.filter(name='partner')[0])
        notification_android_device = FCMDeviceFactory(type='android')
        notification_ios_device = FCMDeviceFactory(type='ios')
        notification_web_device = FCMDeviceFactory(type='web')

        notification_settings.fcm_device.add(notification_android_device, notification_ios_device,
                                             notification_web_device)
        Notification.send_notification(user=user, title=notification.title,
                                       title_ru=notification.title_ru,
                                       description=notification.description,
                                       description_ru=notification.description_ru,
                                       mode=notification.mode.name,
                                       notification_id=notification.id,
                                       organization=notification.organization,
                                       type=notification.type,
                                       extra_data=notification.extra_data)
        self.assertEqual(mocked_send_message.call_count, 0)
