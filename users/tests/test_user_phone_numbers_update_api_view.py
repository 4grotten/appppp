import json
from unittest import expectedFailure

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from users.tests.factories import (
    UserFactory,
    PhoneNumberFactory,
)


class UserPhoneNumbersUpdateAPIViewTestCase(APITransactionTestCase):
    url_name = "v1:set_user_phones"

    @classmethod
    def setUpClass(cls):
        cls.user = UserFactory(phone_number="996550979133")
        cls.phone_number_one = PhoneNumberFactory(user=cls.user)
        cls.phone_number_two = PhoneNumberFactory(user=cls.user)
        cls.phone_number_three = PhoneNumberFactory(user=cls.user)

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
            "errors": {'phone_numbers': ['This field is required.']}
        }

        response = self.client.post(
            reverse(self.url_name),
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    @expectedFailure
    def test_update_user_phone_numbers(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "phone_numbers": ["996550778151", "996550778152", "996550778153"]
        }
        expected_data = {
            "message": "Successfully updated",
            "numbers": [
                {
                    "id": self.phone_number_one.id,
                    "phone_number": "996550778151"
                },
                {
                    "id": self.phone_number_two.id,
                    "phone_number": "996550778152"
                },
                {
                    "id": self.phone_number_three.id,
                    "phone_number": "996550778153"
                },
            ]
        }

        response = self.client.post(
            reverse(self.url_name),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
