import json
from unittest import expectedFailure

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import (
    OrganizationFactory, OrganizationPhoneNumberFactory
)
from users.tests.factories import UserFactory


class OrgPhonesListAPIViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550778133")
        self.organization = OrganizationFactory(
            owner=self.user
        )
        self.org_phone_number = OrganizationPhoneNumberFactory(
            organization=self.organization,
            phone_number="996550778133"
        )

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.post(
            reverse(
                "v1:organization_phones",
                kwargs={"pk": self.organization.id}
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_required_fields(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "phone_numbers": ["This field is required."]
            }
        }
        response = self.client.post(
            reverse("v1:organization_phones", kwargs={"pk": self.organization.id}),
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_organization_phones_list(self):
        self.client.force_authenticate(user=self.user)
        expected_data = [
            {
                'id': self.org_phone_number.id,
                'phone_number': self.org_phone_number.phone_number
            }
        ]

        response = self.client.get(
            reverse("v1:organization_phones", kwargs={"pk": self.organization.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    @expectedFailure
    def test_organization_phone_numbers(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "phone_numbers": ["996550778132", "996550888899"]
        }
        expected_data = {
            "message": "Successfully updated",
            "numbers": [
                {

                }
            ]
        }

        response = self.client.post(
            reverse(
                "v1:organization_phones",
                kwargs={"pk": self.organization.id}
            ),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
