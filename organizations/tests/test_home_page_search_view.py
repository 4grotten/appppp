import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import OrganizationFactory, \
    PartnershipFactory
from users.tests.factories import UserFactory


class HomepageSearchViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("v1:homepage_search_partners")
        self.user = UserFactory()
        self.org_one = OrganizationFactory(owner=self.user)
        self.org_two = OrganizationFactory(owner=self.user)

    def test_get_organizations_without_partner_id(self):
        expected_data = {
            "total_count": 2,
            "total_pages": 1,
            "list": [
                {
                    "id": self.org_one.id,
                    "promo_cashback": None,
                    "image": {
                        "id": self.org_one.image.id,
                        "file": f"{self.org_one.image.file.url}",
                        "name": os.path.basename(str(self.org_one.image.file)),
                        "large": f"{self.org_one.image.large.url}",
                        "medium": f"{self.org_one.image.medium.url}",
                        "small": f"{self.org_one.image.small.url}",
                    },
                    "title": self.org_one.title,
                    "types": [],
                    "discounts": [],
                    "verification_status": self.org_one.verification_status
                },
                {
                    "id": self.org_two.id,
                    "promo_cashback": None,
                    "image": {
                        "id": self.org_two.image.id,
                        "file": f"{self.org_two.image.file.url}",
                        "name": os.path.basename(str(self.org_two.image.file)),
                        "large": f"{self.org_two.image.large.url}",
                        "medium": f"{self.org_two.image.medium.url}",
                        "small": f"{self.org_two.image.small.url}",
                    },
                    "title": self.org_two.title,
                    "types": [],
                    "discounts": [],
                    "verification_status": self.org_two.verification_status
                },
            ]
        }

        response = self.client.get(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_organizations_with_parameter_partner(self):
        partner = PartnershipFactory(
            requested_by=self.org_one,
            accepted_by=self.org_two,
            is_accepted=True,
            can_share_cashback=True
        )
        query_params = {
            "partner": partner.requested_by.id
        }
        expected_data = {
            "total_count": 1,
            "total_pages": 1,
            "list": [
                {
                    "id": partner.accepted_by.id,
                    "title": partner.accepted_by.title,
                    "promo_cashback": None,
                    "discounts": [],
                    "types": [],
                    "image": {
                        "id": partner.accepted_by.image.id,
                        "file": f"{partner.accepted_by.image.file.url}",
                        "name": os.path.basename(str(partner.accepted_by.image.file)),
                        "large": f"{partner.accepted_by.image.large.url}",
                        "medium": f"{partner.accepted_by.image.medium.url}",
                        "small": f"{partner.accepted_by.image.small.url}",
                    },
                    "verification_status": partner.accepted_by.verification_status
                },
            ]
        }

        response = self.client.get(
            self.url,
            query_params,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
