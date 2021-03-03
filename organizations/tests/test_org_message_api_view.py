import json
import os
from unittest.mock import patch, Mock, call

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Message
from organizations.tests.factories import (
    OrganizationFactory, MessageFactory, MembershipFactory
)
from users.tests.factories import UserFactory


class OrgMessageAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory(
            full_name="Johnny Sins",
            username="PornActor"
        )
        self.organization = OrganizationFactory(owner=self.user)

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.get(
            reverse("v1:organization_messages", kwargs={
                "pk": self.organization.id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_required_fields(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "content": ["This field is required."],
            }
        }

        response = self.client.post(
            reverse("v1:organization_messages", kwargs={
                "pk": self.organization.id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_organization_messages(self):
        self.client.force_authenticate(user=self.user)
        user_receiver_one = UserFactory(full_name="Какой-то чертила")
        user_receiver_two = UserFactory(full_name="Какой-то чертила номер два")
        organization_two = OrganizationFactory()
        organization_three = OrganizationFactory()
        message_one = MessageFactory(
            sender=self.user,
            organization=self.organization,
            content="Здесь да какая-нибудь хуйня",
            message_to=Message.ORGANIZATION_FOLLOWERS,
        )
        membership = MembershipFactory(
            organization=self.organization,
            user=self.user
        )
        message_one.receivers.add(user_receiver_one.id)
        message_one.receivers.add(user_receiver_two.id)
        message_one.receiver_partners.add(organization_two.id)
        message_one.receiver_partners.add(organization_three.id)
        expected_data = {
            "total_count": 1,
            "total_pages": 1,
            "list": [
                {
                    "id": message_one.id,
                    "sender": {
                        "id": self.user.id,
                        "full_name": self.user.full_name,
                        "avatar": {
                            "id": self.user.avatar.id,
                            "file": f"http://testserver{self.user.avatar.file.url}",
                            "name": os.path.basename(
                                self.user.avatar.file.name),
                            "large": f"http://testserver{self.user.avatar.large.url}",
                            "medium": f"http://testserver{self.user.avatar.medium.url}",
                            "small": f"http://testserver{self.user.avatar.small.url}",
                        },
                        "username": self.user.username,
                    },
                    "message_to": message_one.message_to,
                    "content": message_one.content,
                    "created_at": message_one.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "receivers_count": 2,
                    "receivers": [
                        {
                            "id": user_receiver_two.id,
                            "full_name": user_receiver_two.full_name,
                            "avatar": {
                                "id": user_receiver_two.avatar.id,
                                "file": f"http://testserver{user_receiver_two.avatar.file.url}",
                                "name": os.path.basename(
                                    user_receiver_two.avatar.file.name),
                                "large": f"http://testserver{user_receiver_two.avatar.large.url}",
                                "medium": f"http://testserver{user_receiver_two.avatar.medium.url}",
                                "small": f"http://testserver{user_receiver_two.avatar.small.url}",
                            },
                            "username": None
                        },
                        {
                            "id": user_receiver_one.id,
                            "full_name": user_receiver_one.full_name,
                            "avatar": {
                                "id": user_receiver_one.avatar.id,
                                "file": f"http://testserver{user_receiver_one.avatar.file.url}",
                                "name": os.path.basename(
                                    user_receiver_one.avatar.file.name),
                                "large": f"http://testserver{user_receiver_one.avatar.large.url}",
                                "medium": f"http://testserver{user_receiver_one.avatar.medium.url}",
                                "small": f"http://testserver{user_receiver_one.avatar.small.url}",
                            },
                            "username": None
                        },
                    ],
                    "sender_role": membership.role.title,
                    "receiver_partner_count": 2,
                    "receiver_partners": [
                        {
                            "id": organization_two.id,
                            "title": organization_two.title,
                            "image": {
                                "id": organization_two.image.id,
                                "file": f"http://testserver{organization_two.image.file.url}",
                                "name": os.path.basename(organization_two.image.file.name),
                                "large": f"http://testserver{organization_two.image.large.url}",
                                "medium": f"http://testserver{organization_two.image.medium.url}",
                                "small": f"http://testserver{organization_two.image.small.url}",
                            }
                        },
                        {
                            "id": organization_three.id,
                            "title": organization_three.title,
                            "image": {
                                "id": organization_three.image.id,
                                "file": f"http://testserver{organization_three.image.file.url}",
                                "name": os.path.basename(
                                    organization_three.image.file.name),
                                "large": f"http://testserver{organization_three.image.large.url}",
                                "medium": f"http://testserver{organization_three.image.medium.url}",
                                "small": f"http://testserver{organization_three.image.small.url}",
                            }
                        }
                    ],
                }
            ]
        }

        response = self.client.get(
            reverse("v1:organization_messages", kwargs={
                "pk": self.organization.id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_user_can_not_to_create_organization_message(self):
        another_user = UserFactory()
        self.client.force_authenticate(user=another_user)
        data = {
            "content": "Тут какое-то сообщение от Ахмеда",
            "message_to": Message.ORGANIZATION_FOLLOWERS
        }
        expected_data = {
            "message": "No rights to send message to followers of this organization"
        }

        response = self.client.post(
            reverse("v1:organization_messages", kwargs={
                "pk": self.organization.id
            }),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content, expected_data)

    @patch("organizations.services.organization_services.OrgMessageService.send_message")
    def test_send_organization_message(
            self, send_message_mock: Mock,):
        self.client.force_authenticate(user=self.user)
        data = {
            "content": "Тут какое-то сообщение от Ахмеда",
            "message_to": Message.ORGANIZATION_FOLLOWERS
        }
        expected_data = {
            "message": "Message is created"
        }

        response = self.client.post(
            reverse("v1:organization_messages", kwargs={
                "pk": self.organization.id
            }),
            data=json.dumps(data),
            content_type='application/json'
        )

        send_message_mock.assert_has_calls([
            call(
                organization=self.organization,
                content=data.get("content"),
                sender=self.user,
                message_to=data.get("message_to")
            )
        ])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content, expected_data)
