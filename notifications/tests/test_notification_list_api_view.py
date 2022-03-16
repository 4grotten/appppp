import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from notifications.tests.factories import NotificationFactory
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory


class NotificationListAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.get(
            reverse("v1:own_notifications"),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_notification_list(self):
        self.organization = OrganizationFactory(owner=self.user)
        self.notification_one = NotificationFactory(
            recipient=self.user, organization=self.organization
        )
        self.notification_two = NotificationFactory(
            recipient=self.user, organization=self.organization
        )
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "total_count": 2,
            "total_pages": 1,
            "list": [
                {
                    "id": self.notification_two.id,
                    "created_at": self.notification_two.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "updated_at": self.notification_two.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "sender": self.notification_two.sender,
                    "extra_data": self.notification_two.extra_data,
                    "mode": self.notification_two.mode,
                    "title": self.notification_two.title,
                    "description": self.notification_two.description,
                    "is_read": self.notification_two.is_read,
                    "organization": {
                        "id": self.organization.id,
                        "title": self.organization.title,
                        "image": {
                            "id": self.organization.image.id,
                            "file": f"{self.organization.image.file.url}",
                            "name": os.path.basename(
                                str(self.organization.image.file)),
                            "large": f"{self.organization.image.large.url}",
                            "medium": f"{self.organization.image.medium.url}",
                            "small": f"{self.organization.image.small.url}",
                        },
                        "address": self.organization.address,
                        "verification_status": self.organization.verification_status,
                    },
                    "type": self.notification_two.type,
                },
                {
                    "id": self.notification_one.id,
                    "created_at": self.notification_one.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "updated_at": self.notification_one.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "sender": self.notification_one.sender,
                    "extra_data": self.notification_one.extra_data,
                    "mode": self.notification_one.mode,
                    "title": self.notification_one.title,
                    "description": self.notification_one.description,
                    "is_read": self.notification_one.is_read,
                    "organization": {
                        "id": self.organization.id,
                        "title": self.organization.title,
                        "image": {
                            "id": self.organization.image.id,
                            "file": f"{self.organization.image.file.url}",
                            "name": os.path.basename(
                                str(self.organization.image.file)),
                            "large": f"{self.organization.image.large.url}",
                            "medium": f"{self.organization.image.medium.url}",
                            "small": f"{self.organization.image.small.url}",
                        },
                        "address": self.organization.address,
                        "verification_status": self.organization.verification_status,
                    },
                    "type": self.notification_one.type,
                }
            ]
        }

        response = self.client.get(
            reverse("v1:own_notifications"),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)
