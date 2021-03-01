import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.services.organization_services import OrganizationService
from organizations.tests.factories import (
    OrganizationFactory, OrganizationPhoneNumberFactory
)
from users.tests.factories import UserFactory
from common.tests.factories import CurrencyFactory


class OrgPhonesListAPIViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550778133")
        self.organization = OrganizationFactory(
            owner=self.user
        )

    # def test_user_unauthorized(self):
    #     expected_data = {
    #         "detail": "Authentication credentials were not provided."
    #     }
    #
    #     response = self.client.post(
    #         reverse("v1:organization_phones", kwargs={"pk": self.organization.id}),
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
    #             "phone_numbers": ["This field is required."]
    #         }
    #     }
    #     response = self.client.post(
    #         reverse("v1:organization_phones", kwargs={"pk": self.organization.id}),
    #         data=json.dumps({}),
    #         content_type='application/json'
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
    #     self.assertJSONEqual(response.content, expected_data)
    #
    # def test_get_list_organizations(self):
    #     self.client.force_authenticate(user=self.user)
    #     organization_one = OrganizationFactory(owner=self.user)
    #     organization_two = OrganizationFactory(owner=self.user)
    #     organization_three = OrganizationFactory(owner=self.user)
    #     expected_data = {
    #         "list": [{
    #             "id": organization_one.id,
    #             "image": organization_one.image,
    #             "role": OrganizationService.get_user_role_in_organization(
    #                 organization=organization_one, user=self.user
    #             ),
    #             "title": organization_one.title
    #         },
    #         {
    #             "id": organization_two.id,
    #             "image": organization_two.image,
    #             "role": OrganizationService.get_user_role_in_organization(
    #                 organization=organization_two, user=self.user
    #             ),
    #             "title": organization_two.title
    #         },
    #         {
    #             "id": organization_three.id,
    #             "image": organization_three.image,
    #             "role": OrganizationService.get_user_role_in_organization(
    #                 organization=organization_three, user=self.user
    #             ),
    #             "title": organization_three.title
    #         }
    #         ],
    #         "total_count": 3,
    #         "total_pages": 1
    #     }
    #
    #     response = self.client.get(
    #         reverse("v1:organization_phones", kwargs={"pk": self.organization.id}),
    #         content_type='application/json'
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertJSONEqual(response.content, expected_data)

    def test_get_org_phones_list(self):
        self.client.force_authenticate(user=self.user)
        organization_phone_number_one = OrganizationPhoneNumberFactory(
            organization=self.organization,
            phone_number="996700353819"
        )
        expected_data = [
            {
                "id": organization_phone_number_one.id,
                "phone_number": str(organization_phone_number_one.phone_number)
            }
        ]

        response = self.client.get(
            reverse("v1:organization_phones", kwargs={"pk": self.organization.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
