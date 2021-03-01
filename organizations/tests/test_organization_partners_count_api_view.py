import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import (
    OrganizationFactory, PartnershipFactory
)
from users.tests.factories import UserFactory


class OrganizationPartnersCountAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user_one = UserFactory()
        self.user_two = UserFactory()
        self.org_requested_by = OrganizationFactory(owner=self.user_one)
        self.org_accepted_by = OrganizationFactory(owner=self.user_two)
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
                "v1:org_get_partners_count",
                kwargs={"pk": self.partner.requested_by.id}
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_organization_followers(self):
        self.client.force_authenticate(user=self.user_one)
        expected_data = {
            "partners": [{
                "id": self.partner.accepted_by.id,
                "image": {
                    "id": self.partner.accepted_by.image.id,
                    "file": f"http://testserver{self.partner.accepted_by.image.file.url}",
                    "name": os.path.basename(
                        str(self.partner.accepted_by.image.file)),
                    "large": f"http://testserver{self.partner.accepted_by.image.large.url}",
                    "medium": f"http://testserver{self.partner.accepted_by.image.medium.url}",
                    "small": f"http://testserver{self.partner.accepted_by.image.small.url}",
                },
                "title": self.partner.accepted_by.title,
            }],
            "count": 1
        }

        response = self.client.get(
            reverse(
                "v1:org_get_partners_count",
                kwargs={"pk": self.partner.requested_by.id}
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
