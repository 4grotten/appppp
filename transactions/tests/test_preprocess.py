import json

from django.urls import reverse
from rest_framework.test import APITestCase

from organizations.tests.factories import (
    OrganizationFactory, OrganizationClientFinancialStatusFactory, PartnershipFactory
)
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

    def test_correct_corporate_organizations_accrued_cashback(self):
        partner_owner = UserFactory()

        partner_organization = OrganizationFactory(owner=partner_owner)
        PartnershipFactory(
            requested_by=self.organization, accepted_by=partner_organization,
            is_accepted=True, can_share_cashback=True
        )
        PartnershipFactory(
            requested_by=partner_organization, accepted_by=self.organization,
            is_accepted=True, can_share_cashback=True
        )
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=partner_organization, card=None, accrued_cashback=300
        )

        no_mutually_shared_organization = OrganizationFactory(owner=partner_owner)
        PartnershipFactory(
            requested_by=self.organization, accepted_by=no_mutually_shared_organization,
            is_accepted=True, can_share_cashback=False
        )
        PartnershipFactory(
            requested_by=no_mutually_shared_organization, accepted_by=self.organization,
            is_accepted=True, can_share_cashback=True
        )
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=no_mutually_shared_organization, card=None, accrued_cashback=2000
        )

        non_partner_organization = OrganizationFactory(owner=partner_owner)
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=non_partner_organization, card=None, accrued_cashback=1000
        )

        data = {
            "client": self.client_user.id,
            "organization": self.organization.id
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['accrued_cashback'], 800)
