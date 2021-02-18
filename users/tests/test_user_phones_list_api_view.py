from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
    PhoneNumberFactory,
)


class UserPhonesListAPIViewTestCase(APITestCase):
    url_name = "v1:user_phones"

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(phone_number="996550779133")

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.get(
            reverse(self.url_name, kwargs={"pk": self.user.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_user_phones_list(self):
        phone_number_one = PhoneNumberFactory(user=self.user)
        phone_number_two = PhoneNumberFactory(user=self.user)
        phone_number_three = PhoneNumberFactory(user=self.user)
        self.client.force_authenticate(user=self.user)
        expected_data = [
            {
                "id": phone_number_one.id,
                "phone_number": phone_number_one.phone_number
            },
            {
                "id": phone_number_two.id,
                "phone_number": phone_number_two.phone_number
            },
            {
                "id": phone_number_three.id,
                "phone_number": phone_number_three.phone_number
            },
        ]

        response = self.client.get(
            reverse(self.url_name, kwargs={"pk": self.user.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
