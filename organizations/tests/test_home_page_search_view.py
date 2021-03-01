import json
import os
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from common.tests.factories import FileFactory
from organizations.tests.factories import OrganizationFactory, PartnershipFactory
from users.tests.factories import UserFactory


class HomepageSearchViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = reverse("v1:homepage_search")
        self.user = UserFactory()

    # def test_get_organizations_without_partner_id(self):
    #     expected_data = {
    #         "total_count": 3,
    #         "total_pages": 1,
    #         "list": [
    #             {
    #                 "id": self.org_one.id,
    #                 "image": {
    #                     "id": self.org_one.image.id,
    #                     "file": f"http://testserver{self.org_one.image.file.url}",
    #                     "name": os.path.basename(str(self.org_one.image.file)),
    #                     "large": f"http://testserver{self.org_one.image.large.url}",
    #                     "medium": f"http://testserver{self.org_one.image.medium.url}",
    #                     "small": f"http://testserver{self.org_one.image.small.url}",
    #                 },
    #                 "title": self.org_one.title,
    #                 "types": [],
    #                 "discounts": [],
    #             },
    #             {
    #                 "id": self.org_two.id,
    #                 "image": {
    #                     "id": self.org_two.image.id,
    #                     "file": f"http://testserver{self.org_two.image.file.url}",
    #                     "name": os.path.basename(str(self.org_two.image.file)),
    #                     "large": f"http://testserver{self.org_two.image.large.url}",
    #                     "medium": f"http://testserver{self.org_two.image.medium.url}",
    #                     "small": f"http://testserver{self.org_two.image.small.url}",
    #                 },
    #                 "title": self.org_two.title,
    #                 "types": [],
    #                 "discounts": [],
    #             },
    #             {
    #                 "id": self.org_three.id,
    #                 "image": {
    #                     "id": self.org_three.image.id,
    #                     "file": f"http://testserver{self.org_three.image.url}",
    #                     "name": os.path.basename(str(self.org_three.image.file)),
    #                     "large": f"http://testserver{self.org_three.image.large.url}",
    #                     "medium": f"http://testserver{self.org_three.image.medium.url}",
    #                     "small": f"http://testserver{self.org_three.image.small.url}",
    #                 },
    #                 "title": self.org_three.title,
    #                 "types": [],
    #                 "discounts": [],
    #             }
    #         ]
    #     }
    #
    #     response = self.client.get(
    #         self.url,
    #         content_type='application/json'
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertJSONEqual(response.content, expected_data)

    def test_get_organizations_with_parameter_partner(self):
        partner = PartnershipFactory(
            requested_by=self.org_one,
            accepted_by=self.org_two,
            is_accepted=True,
            can_share_cashback=True
        )
        quary_params = {
            "partner": partner.id
        }
        expected_data = {
            "total_count": 1,
            "total_pages": 1,
            "list": [
                {
                    "id": self.org_one.id,
                    "image": {
                        "id": partner.requested_by.image.id,
                        "file": f"http://testserver{self.org_one.image.file.url}",
                        "name": os.path.basename(str(partner.requested_by.image.file)),
                        "large": f"http://testserver{partner.requested_by.image.large.url}",
                        "medium": f"http://testserver{partner.requested_by.image.medium.url}",
                        "small": f"http://testserver{partner.requested_by.image.small.url}",
                    },
                    "title": partner.requested_by.title,
                    "types": [],
                    "discounts": [],
                },
            ]
        }

        response = self.client.get(
            self.url,
            quary_params,
            content_type='application/json'
        )

        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
