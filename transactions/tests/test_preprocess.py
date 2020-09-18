import json

from django.urls import reverse
from rest_framework.test import APITestCase

from organizations.tests.factories import OrganizationFactory, OrganizationClientFinancialStatusFactory
from users.tests.factories import UserFactory, TokenFactory


class PreprocessTransactionTestCase(APITestCase):
    def setUp(self):
        self.url = reverse('v1:transaction_preprocess')
        self.user = UserFactory(phone_number='123456789')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}
        self.organization = OrganizationFactory(owner=self.user)

        self.client_user = UserFactory(phone_number='777777777')

        OrganizationClientFinancialStatusFactory(user=self.client_user, organization=self.organization, card=None,
                                                 accrued_cashback=500)

    def test_correct_single_organization_accrued_cashback(self):
        data = {
            "client": self.client_user.id,
            "organization": self.organization.id
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['accrued_cashback'], 500)
