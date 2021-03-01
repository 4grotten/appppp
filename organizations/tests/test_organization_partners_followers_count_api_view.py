import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import (
    OrganizationFactory, PartnershipFactory, SubscriptionFactory,
)
from users.tests.factories import UserFactory


class OrganizationPartnersFollowersCountAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user_one = UserFactory()
        self.user_two = UserFactory(
            full_name="Владимир Путин",
            username="VladimirPutin228"
        )
        self.org_requested_by = OrganizationFactory(owner=self.user_one)
        self.org_accepted_by = OrganizationFactory(owner=self.user_two)
        self.subscription = SubscriptionFactory(
            user=self.user_two, organization=self.org_accepted_by
        )
        self.partner = PartnershipFactory(
            requested_by=self.org_requested_by,
            accepted_by=self.org_accepted_by,
            is_accepted=True,
        )

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.get(
            reverse(
                "v1:org_partners_followers_count",
                kwargs={"pk": self.partner.requested_by.id}
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_organization_partners_followers_and_count(self):
        self.client.force_authenticate(user=self.user_one)
        expected_data = {
            "followers": [
                {
                    "id": self.org_accepted_by.owner.id,
                    "full_name": self.org_accepted_by.owner.full_name,
                    "username": self.org_accepted_by.owner.username,
                    "avatar": {
                        "id": self.org_accepted_by.owner.avatar.id,
                        "file": f"http://testserver{self.org_accepted_by.owner.avatar.file.url}",
                        "name": os.path.basename(self.org_accepted_by.owner.avatar.file.name),
                        "large": f"http://testserver{self.org_accepted_by.owner.avatar.large.url}",
                        "medium": f"http://testserver{self.org_accepted_by.owner.avatar.medium.url}",
                        "small": f"http://testserver{self.org_accepted_by.owner.avatar.small.url}",
                    },
                }
            ],
            "count": 1
        }

        response = self.client.get(
            reverse(
                "v1:org_partners_followers_count",
                kwargs={"pk": self.org_requested_by.id}
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
