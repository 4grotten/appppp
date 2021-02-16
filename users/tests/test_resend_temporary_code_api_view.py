import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.exceptions import ObjectNotFoundException
from users.constants import CHANGE_AUTH_NUMBER_TYPE, REGISTER_AUTH_TYPE
from users.tests.factories import (
    UserFactory,
    TemporaryPhoneNumberFactory,
)


class ResendTemporaryCodeAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:resend_code')

    def test_required_fields(self):
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "phone_number": ["This field is required."],
                "type": ["This field is required."],
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_temporary_codes_not_found(self):
        data = {
            "phone_number": "996550178133",
            "type": CHANGE_AUTH_NUMBER_TYPE
        }

        self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertRaises(ObjectNotFoundException)

    def test_create_temporary_phone_number(self):
        user = UserFactory(phone_number="996550178133")
        TemporaryPhoneNumberFactory(phone_number=user.phone_number)
        data = {
            "phone_number": user.phone_number,
            "type": CHANGE_AUTH_NUMBER_TYPE
        }
        expected_data = {
            "message": "Code has successfully sent"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_create_and_send_temporary_code(self):
        user = UserFactory(phone_number="996550278133")
        data = {
            "phone_number": user.phone_number,
            "type": REGISTER_AUTH_TYPE
        }
        expected_data = {
            "message": "Code has successfully sent"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
