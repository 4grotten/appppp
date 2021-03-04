import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import OrganizationFactory
from users.tests.factories import (
    UserFactory,
    TokenFactory,
)
from shop.tests.factories import ShopItemFactory


class ItemChangePublishedStatusViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("v1:item_published_status")

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

    def test_required_fields(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "item": ["This field is required."],
                "is_published": ["This field is required."],
            }
        }

        response = self.client.post(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_change_item_published_status(self):
        self.client.force_authenticate(user=self.user)
        organization = OrganizationFactory(owner=self.user)
        item = ShopItemFactory(organization=organization)
        data = {
            "item": item.id,
            "is_published": True
        }
        expected_data = {
            "message": "Successfully updated published status"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
