from django.contrib.auth import get_user_model
from django.db import models
from fcm_django.models import FCMDevice

from common.models import TimestampModel
from organizations.models import Organization
from django.conf import settings

from shop.models import ShopItem
from .constants import (get_titles_descriptions_from_type,
                        NOTIFICATION_MODE_DISCOUNT,
                        NOTIFICATION_MODES,
                        NOTIFICATION_MODE_SYSTEM, NOTIFICATION_MODE_PARTNER,
                        NOTIFICATION_TYPES, SYSTEM_TYPE, NOTIFICATION_MODE_PERSONAL, NOTIFICATION_MODE_PRODUCT,
                        NOTIFICATION_MODE_RENTAL, NOTIFICATION_MODE_TICKET, NOTIFICATION_MODE_RESUME)

User = get_user_model()


class NotificationMode(TimestampModel):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class Notification(TimestampModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipient_notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                               related_name='sender_notifications')
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_read = models.BooleanField(default=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='organization_notifications')

    item = models.ForeignKey('shop.ShopItem', on_delete=models.SET_NULL, blank=True, null=True,
                             related_name='shopitem_notifications')
    mode = models.CharField(max_length=255, choices=NOTIFICATION_MODES)
    type = models.CharField(max_length=255, choices=NOTIFICATION_TYPES, default=SYSTEM_TYPE)
    extra_data = models.JSONField(null=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            notification_str = get_titles_descriptions_from_type(notification_type=self.type,
                                                                 extra_data=self.extra_data)
            self.title = notification_str['title']
            self.description = notification_str['description']
            self.title_ru = notification_str['title_ru']
            self.description_ru = notification_str['description_ru']
            self.title_de = notification_str['title_de']
            self.description_de = notification_str['description_de']
            self.title_tr = notification_str['title_tr']
            self.description_tr = notification_str['description_tr']
            self.title_zh = notification_str['title_zh']
            self.description_zh = notification_str['description_zh']
        super().save(*args, **kwargs)

        self.send_notification(
            user=self.recipient,
            type=self.type,
            title=self.title,
            title_ru=self.title_ru,
            title_de=self.title_de,
            title_tr=self.title_tr,
            title_zh=self.title_zh,
            description=self.description,
            description_ru=self.description_ru,
            description_de=self.description_de,
            description_tr=self.description_tr,
            description_zh=self.description_zh,
            mode=self.mode,
            notification_id=self.id,
            organization=self.organization,
            item=self.item,
            extra_data=self.extra_data
        )

    @classmethod
    def send_notification(cls, user: User, title: str, title_ru: str, title_de: str, title_tr: str, title_zh: str,
                          description: str, description_ru: str, description_de: str, description_tr: str,
                          description_zh: str, notification_id: int, mode: str, type: str,
                          organization=None, extra_data=None, item=None):
        organization_image = cls.get_organization_small_image(organization=organization) if organization else None,
        image = cls.get_item_small_image(item=item) if type == 'new_comment' else organization_image
        if not NotificationSetting.objects.filter(user=user).exists():
            return

        notification_setting = NotificationSetting.objects.get(user=user)

        if not ((mode == NOTIFICATION_MODE_DISCOUNT and notification_setting.discount_notifications) or
                (mode == NOTIFICATION_MODE_PERSONAL and notification_setting.private_notifications) or
                (mode == NOTIFICATION_MODE_SYSTEM and notification_setting.private_notifications) or
                (mode == NOTIFICATION_MODE_PARTNER and notification_setting.organization_notifications) or
                (mode == NOTIFICATION_MODE_PRODUCT and notification_setting.product_notifications) or
                (mode == NOTIFICATION_MODE_RENTAL and notification_setting.rental_notifications) or
                (mode == NOTIFICATION_MODE_TICKET and notification_setting.ticket_notifications) or
                (mode == NOTIFICATION_MODE_RESUME and notification_setting.resume_notifications)
        ):
            return
        notification_payload = {
            'title': title,
            'body': description,
            'click_action': type,
            'sound': 'default',
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_ru = {
            'title': title_ru,
            'body': description_ru,
            'click_action': type,
            'sound': 'default',
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_de = {
            'title': title_de,
            'body': description_de,
            'click_action': type,
            'sound': 'default',
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_tr = {
            'title': title_tr,
            'body': description_tr,
            'click_action': type,
            'sound': 'default',
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_zh = {
            'title': title_zh,
            'body': description_zh,
            'click_action': type,
            'sound': 'default',
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_web = {
            'data': {
                'title': title,
                'body': description,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type,
                'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            },

            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_web_ru = {
            'data': {
                'title': title_ru,
                'body': description_ru,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type,
                'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            },

            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_web_de = {
            'data': {
                'title': title_de,
                'body': description_de,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type,
                'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            },

            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_web_tr = {
            'data': {
                'title': title_tr,
                'body': description_tr,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type,
                'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            },

            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_web_zh = {
            'data': {
                'title': title_zh,
                'body': description_zh,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type,
                'icon': cls.get_organization_small_image(organization=organization) if organization else None,
            },

            'extra_kwargs': {
                'mutable_content': True,
            },
        }

        notification_payload_android = {
            'data': {
                'title': title,
                'body': description,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            }
        }

        notification_payload_ru_android = {
            'data': {
                'title': title_ru,
                'body': description_ru,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            }
        }

        notification_payload_de_android = {
            'data': {
                'title': title_de,
                'body': description_de,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            }
        }

        notification_payload_tr_android = {
            'data': {
                'title': title_tr,
                'body': description_tr,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            }
        }

        notification_payload_zh_android = {
            'data': {
                'title': title_zh,
                'body': description_zh,
                'click_action': type,
                'sound': 'default',
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'item': {
                    'id': item.id,
                    'name': item.name,
                } if item else None,
                'image': image,
                'extra_data': extra_data,
                'type': type
            }
        }

        fcm_devices_ru = notification_setting.fcm_device.filter(settingstotoken__language='ru', type='ios')
        fcm_devices_ru.send_message(**notification_payload_ru, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_en = notification_setting.fcm_device.filter(settingstotoken__language='en', type='ios')
        fcm_devices_en.send_message(**notification_payload, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_de = notification_setting.fcm_device.filter(settingstotoken__language='de', type='ios')
        fcm_devices_de.send_message(**notification_payload_de, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_tr = notification_setting.fcm_device.filter(settingstotoken__language='tr', type='ios')
        fcm_devices_tr.send_message(**notification_payload_tr, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_zh = notification_setting.fcm_device.filter(settingstotoken__language='zh', type='ios')
        fcm_devices_zh.send_message(**notification_payload_zh, dry_run=settings.FCM_DRY_RUN_ENABLE)

        fcm_devices_ru_web = notification_setting.fcm_device.filter(settingstotoken__language='ru', type='web')
        fcm_devices_ru_web.send_message(**notification_payload_web_ru, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_en_web = notification_setting.fcm_device.filter(settingstotoken__language='en', type='web')
        fcm_devices_en_web.send_message(**notification_payload_web, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_de_web = notification_setting.fcm_device.filter(settingstotoken__language='de', type='web')
        fcm_devices_de_web.send_message(**notification_payload_web_de, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_tr_web = notification_setting.fcm_device.filter(settingstotoken__language='tr', type='web')
        fcm_devices_tr_web.send_message(**notification_payload_web_tr, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_zh_web = notification_setting.fcm_device.filter(settingstotoken__language='zh', type='web')
        fcm_devices_zh_web.send_message(**notification_payload_web_zh, dry_run=settings.FCM_DRY_RUN_ENABLE)


        fcm_devices_ru_android = notification_setting.fcm_device.filter(settingstotoken__language='ru', type='android')
        fcm_devices_ru_android.send_message(**notification_payload_ru_android, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_en_android = notification_setting.fcm_device.filter(settingstotoken__language='en', type='android')
        fcm_devices_en_android.send_message(**notification_payload_android, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_de_android = notification_setting.fcm_device.filter(settingstotoken__language='de', type='android')
        fcm_devices_de_android.send_message(**notification_payload_de_android, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_tr_android = notification_setting.fcm_device.filter(settingstotoken__language='tr', type='android')
        fcm_devices_tr_android.send_message(**notification_payload_tr_android, dry_run=settings.FCM_DRY_RUN_ENABLE)
        fcm_devices_zh_android = notification_setting.fcm_device.filter(settingstotoken__language='zh', type='android')
        fcm_devices_zh_android.send_message(**notification_payload_zh_android, dry_run=settings.FCM_DRY_RUN_ENABLE)


    @staticmethod
    def get_organization_small_image(organization: Organization):
        return organization.image.medium.url if organization.image else None

    @staticmethod
    def get_item_small_image(item: ShopItem):
        return item.images.first().medium.url if item else None


# FIXME: Add type field and get rid of 5 diffrent types of notifications.
class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ManyToManyField(FCMDevice, through='SettingsToToken')
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=False)
    product_notifications = models.BooleanField(default=True)
    delivery_notifications = models.BooleanField(default=True)
    rental_notifications = models.BooleanField(default=True)
    ticket_notifications = models.BooleanField(default=True)
    resume_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)


class SettingsToToken(TimestampModel):
    ENGLISH = 'en'
    RUSSIAN = 'ru'
    TURKISH = 'tr'
    GERMAN = 'de'
    CHINESE = 'zh'
    LANGUAGES = (
        (ENGLISH, ENGLISH),
        (RUSSIAN, RUSSIAN),
        (TURKISH, TURKISH),
        (GERMAN, GERMAN),
        (CHINESE, CHINESE)
    )
    notification_settings = models.ForeignKey(NotificationSetting, on_delete=models.CASCADE)
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    language = models.CharField(max_length=25, choices=LANGUAGES, default=RUSSIAN)
