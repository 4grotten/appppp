import json
<<<<<<< HEAD
import unittest
=======
>>>>>>> 31-add-tests-for-registerauthapiview

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
    TokenFactory,
    TemporaryCodeFactory
)


class RegisterAuthApiViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:register_auth')

    # TODO: Need to add phone_number validation
    def test_user_not_register(self):
        data = {
            "phone_number": "huinya kakaya to"
        }
        expected_data = {"message": "Invalid input", "errors": {"phone_number": ["Enter a valid phone number."]}}

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_user_register(self):
        data = {
            "phone_number": "+996550778133"
        }
        expected_data = {
            'message': 'User has successfully created',
            'is_new_user': True,
            'token': None
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_user_found_temporary_code_not_exists(self):
        user = UserFactory(is_new_user=True, phone_number='+996550778133')
        data = {
            "phone_number": str(user.phone_number)
        }
        expected_data = {
            'message': 'User found',
            'is_new_user': True,
            'token': None
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_user_found_with_temporary_code(self):
        user = UserFactory(phone_number="+996550778133", is_new_user=True)
        TemporaryCodeFactory(user=user, is_used=True)
        token = TokenFactory(user=user)
        data = {
            "phone_number": str(user.phone_number)
        }
        expected_data = {
            'message': 'User found',
            'is_new_user': user.is_new_user,
            'token': token.key
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
