import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
    TokenFactory,
    TemporaryCodeFactory
)


class VerifyTemporaryCodeTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:verify_code')

    def test_required_fields(self):
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "code": ["This field is required."],
                "phone_number": ["This field is required."]
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content, expected_data)

    def test_verify_temporary_code(self):
        user = UserFactory(phone_number="996550778133")
        temporary_code = TemporaryCodeFactory(user=user)
        token = TokenFactory(user=user)
        data = {
            "phone_number": user.phone_number,
            "code": temporary_code.code
        }
        expected_data = {
            "message": "Successfully validated",
            "token": token.key,
            "is_new_user": user.is_new_user
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)