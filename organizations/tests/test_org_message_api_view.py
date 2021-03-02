import json
import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.tests.factories import FileFactory
from organizations.models import DiscountCard, Message
from organizations.services.organization_services import OrganizationService
from organizations.tests.factories import OrganizationFactory, MessageFactory, MembershipFactory
from users.tests.factories import UserFactory
from unittest import expectedFailure


class OrgMessageAPIViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.user = UserFactory(
            full_name="Johnny Sins",
            username="PornActor"
        )
        self.organization = OrganizationFactory()

    # def test_user_unauthorized(self):
    #     expected_data = {
    #         "detail": "Authentication credentials were not provided."
    #     }
    #
    #     response = self.client.get(
    #         reverse("v1:organization_messages", kwargs={
    #             "pk": self.organization.id
    #         }),
    #         content_type='application/json'
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertJSONEqual(response.content, expected_data)

    def test_get_organization_messages(self):
        self.client.force_authenticate(user=self.user)
        user_receiver_one = UserFactory()
        user_receiver_two = UserFactory()
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
                    "title": organization_two.title,
                    "content": message_one.content,
                    "message_to": message_one.message_to,
                    "receiver_partner_count": 2,
                    "receiver_partners": [
                        {
                            "id": organization_two.id,
                            "image": {
                                "id": organization_two.owner.avatar.id,
                                "file": f"http://testserver{organization_two.owner.avatar.file.url}",
                                "name": os.path.basename(organization_two.owner.avatar.file.name),
                                "large": f"http://testserver{organization_two.owner.avatar.large.url}",
                                "medium": f"http://testserver{organization_two.owner.avatar.medium.url}",
                                "small": f"http://testserver{organization_two.owner.avatar.small.url}",
                            }
                        },
                        {
                            "id": organization_three.id,
                            "image": {
                                "id": organization_three.owner.avatar.id,
                                "file": f"http://testserver{organization_three.owner.avatar.file.url}",
                                "name": os.path.basename(
                                    organization_three.owner.avatar.file.name),
                                "large": f"http://testserver{organization_three.owner.avatar.large.url}",
                                "medium": f"http://testserver{organization_three.owner.avatar.medium.url}",
                                "small": f"http://testserver{organization_three.owner.avatar.small.url}",
                            }
                        }
                    ],
                    "receivers": [
                        {
                            "avatar": {
                                "id": user_receiver_one.avatar.id,
                                "file": f"http://testserver{user_receiver_one.avatar.file.url}",
                                "name": os.path.basename(user_receiver_one.avatar.file.name),
                                "large": f"http://testserver{user_receiver_one.avatar.large.url}",
                                "medium": f"http://testserver{user_receiver_one.avatar.medium.url}",
                                "small": f"http://testserver{user_receiver_one.avatar.small.url}",
                            }
                        },
                        {
                            "avatar": {
                                "id": user_receiver_two.avatar.id,
                                "file": f"http://testserver{user_receiver_two.avatar.file.url}",
                                "name": os.path.basename(
                                    user_receiver_two.avatar.file.name),
                                "large": f"http://testserver{user_receiver_two.avatar.large.url}",
                                "medium": f"http://testserver{user_receiver_two.avatar.medium.url}",
                                "small": f"http://testserver{user_receiver_two.avatar.small.url}",
                            }
                        }
                    ],
                    "sender": {
                        "id": self.user.id,
                        "full_name": self.user.full_name,
                        "username": self.user.username,
                        "avatar": {
                                "id": self.user.avatar.id,
                                "file": f"http://testserver{self.user.avatar.file.url}",
                                "name": os.path.basename(self.user.avatar.file.name),
                                "large": f"http://testserver{self.user.avatar.large.url}",
                                "medium": f"http://testserver{self.user.avatar.medium.url}",
                                "small": f"http://testserver{self.user.avatar.small.url}",
                            }
                    },
                    "sender_role": membership.role.title,
                    "created_at": message_one.created_at,
                }
            ]
        }

        response = self.client.get(
            reverse("v1:organization_messages", kwargs={
                "pk": self.organization.id
            }),
            content_type='application/json'
        )


        print("=", response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
