import json
import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.tests.factories import FileFactory
from organizations.models import DiscountCard
from organizations.services.organization_services import OrganizationService
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory
from unittest import expectedFailure


class OrganizationsListCreateViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = reverse("v1:user_organizations")
        self.user = UserFactory(phone_number="996550778133")

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.post(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    @expectedFailure
    def test_required_fields(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "accounts": ["This field is required."],
                "cards": ["This field is required."],
                "image_id": ["This field is required."],
                "latitude": ["This field is required."],
                "longitude": ["This field is required."],
                "numbers": ["This field is required."],
                "title": ["This field is required."],
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    @expectedFailure
    def test_get_list_organizations(self):
        self.client.force_authenticate(user=self.user)
        organization_one = OrganizationFactory(owner=self.user)
        organization_two = OrganizationFactory(owner=self.user)
        organization_three = OrganizationFactory(owner=self.user)
        expected_data = {
            "list": [{
                "id": organization_one.id,
                "image": organization_one.image,
                "role": OrganizationService.get_user_role_in_organization(
                    organization=organization_one, user=self.user
                ),
                "title": organization_one.title
            },
            {
                "id": organization_two.id,
                "image": organization_two.image,
                "role": OrganizationService.get_user_role_in_organization(
                    organization=organization_two, user=self.user
                ),
                "title": organization_two.title
            },
            {
                "id": organization_three.id,
                "image": organization_three.image,
                "role": OrganizationService.get_user_role_in_organization(
                    organization=organization_three, user=self.user
                ),
                "title": organization_three.title
            }
            ],
            "total_count": 3,
            "total_pages": 1
        }

        response = self.client.get(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.json(), expected_data)

    @expectedFailure
    def test_create_organization(self):
        self.client.force_authenticate(user=self.user)
        organization_image = FileFactory()
        card_image = FileFactory()
        data = {
            "title": "Ahmed organization",
            "image_id": organization_image.id,
            "numbers": [1, 2],
            "accounts": [1, 2, 3],
            "cards": [{
                "type": DiscountCard.FIXED,
                "percent": 5,
                "image": {
                    "id": card_image.id,
                    "file": f"http://testserver{card_image.file.url}",
                    "name": os.path.basename(card_image.file.name),
                    "large": f"http://testserver{card_image.large.url}",
                    "medium": f"http://testserver{card_image.medium.url}",
                    "small": f"http://testserver{card_image.small.url}",
                }
            }],
            "longitude": -73.989308,
            "latitude": 40.741895,
        }
        expected_data = {

        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.json(), expected_data)
