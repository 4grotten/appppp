import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
)


class ForgotPasswordTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:forgot_password')

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(phone_number="996550770131")

    def test_required_fields(self):
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "phone_number": ["This field is required."],
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_code_sent_for_reset_password(self):
        data = {
            "phone_number": str(self.user.phone_number),
        }
        expected_data = {
            "message": "Code sent"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
