from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
)


class ValidateOldNumberAPIViewTestCase(APITestCase):
    url_name = "v1:validate_old_number"

    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550979133")

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.post(
            reverse(self.url_name),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_validate_old_number(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Code sent to old number and email"
        }

        response = self.client.post(
            reverse(self.url_name),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
