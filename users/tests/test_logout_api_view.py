import json

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory, TokenFactory,
)


class LogoutAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:logout')

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

    def test_user_logout(self):
        user = UserFactory(phone_number="996550778131")
        token = TokenFactory(user=user)
        header = {"HTTP_AUTHORIZATION": f"Token {token.key}"}
        expected_data = {
            "message": "Successfully logged out"
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json',
            **header
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
