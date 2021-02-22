import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
)


class ChangeAndVerifyNewNumberTestCase(APITestCase):
    url_name = "v1:send_code_to_new_number"

    @classmethod
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

    def test_required_fields(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "phone_number": ["This field is required."],
            }
        }

        response = self.client.post(
            reverse(self.url_name),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_send_code_to_new_number_for_user(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "phone_number": str(self.user.phone_number),
        }
        expected_data = {
            "message": "Code sent to new phone number"
        }

        response = self.client.post(
            reverse(self.url_name),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_data)
