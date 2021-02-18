import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
)


class UserChangePasswordTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:change_password')

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_required_fields(self):
        user = UserFactory(phone_number="996550770131")
        self.client.force_authenticate(user=user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "old_password": ["This field is required."],
                "new_password": ["This field is required."],
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_user_change_password(self):
        user = UserFactory(phone_number="996550710131")
        user.set_password("mypasswordnotfound")
        user.save(update_fields=["password"])
        self.client.force_authenticate(user=user)
        data = {
            "old_password": "mypasswordnotfound",
            "new_password": "mynewpassword"
        }
        expected_data = {
            "message": "Password has successfully changed"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
