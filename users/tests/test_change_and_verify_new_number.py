import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from common.exceptions import NotAcceptableException

from users.tests.factories import (
    UserFactory,
    TemporaryCodeFactory,
)


class ChangeAndVerifyNewNumberTestCase(APITestCase):
    url_name = "v1:change_and_verify_new_number"

    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550979133")

    # def test_user_unauthorized(self):
    #     expected_data = {
    #         "detail": "Authentication credentials were not provided."
    #     }
    #
    #     response = self.client.post(
    #         reverse(self.url_name),
    #         content_type='application/json'
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertJSONEqual(response.content, expected_data)
    #
    # def test_required_fields(self):
    #     self.client.force_authenticate(user=self.user)
    #     expected_data = {
    #         "message": "Invalid input",
    #         "errors": {
    #             "old_phone_number": ["This field is required."],
    #             "new_phone_number": ["This field is required."],
    #             "code": ["This field is required."],
    #         }
    #     }
    #
    #     response = self.client.post(
    #         reverse(self.url_name),
    #         content_type='application/json'
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
    #     self.assertJSONEqual(response.content, expected_data)

    def test_user_has_not_permission_for_change_and_verify_number(self):
        self.client.force_authenticate(user=self.user)
        user = UserFactory(phone_number="996550979155")
        code = TemporaryCodeFactory(user=user)
        data = {
            "old_phone_number": str(user.phone_number),
            "new_phone_number": "996550778344",
            "code": code.code
        }

        with self.assertRaisesRegexp(
                NotAcceptableException,
                "You have not permission to do this operation"
        ):
            self.client.post(
                reverse(self.url_name),
                data=json.dumps(data),
                content_type='application/json'
            )
