import json

from django.urls import reverse
from rest_framework.test import APITestCase

from common.tests.factories import CurrencyFactory
from organizations.models import OrganizationClientFinancialStatus, DiscountCard
from organizations.tests.factories import (
    OrganizationFactory, OrganizationClientFinancialStatusFactory, DiscountCardFactory
)
from organizations.tests.test_utils import PartnershipUtils
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class CompleteTransactionTestCase(APITestCase):
    def setUp(self):
        self.url = reverse('v1:transaction_complete')
        self.user = UserFactory(phone_number='123456789')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}

        self.currency = CurrencyFactory(code='XXX')
        self.organization = OrganizationFactory(owner=self.user, currency=self.currency, cashback_group=None)

        self.client_user = UserFactory(phone_number='777777777')

        self.unprocessed_transaction = TransactionFactory(client=self.client_user, processed_by=self.user,
                                                          organization=self.organization, currency=self.currency)

    def test_single_organization_cashback_decreases_when_used(self):
        OrganizationClientFinancialStatusFactory(user=self.client_user, organization=self.organization, card=None,
                                                 accrued_cashback=500)

        data = {
            'transaction_id': self.unprocessed_transaction.id,
            'original_amount': 100,
            'discount_percent': 0,
            'source_card': None,
            'from_cashback': 50,
            "utc_offset_minutes": 0
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        client_status = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                      organization=self.organization)
        self.assertEqual(client_status.accrued_cashback, 450)

    def test_single_organization_cashback_increases_when_cashback_card_is_used(self):
        cashback_card = DiscountCardFactory(organization=self.organization, type=DiscountCard.CASHBACK, percent=15)

        data = {
            'transaction_id': self.unprocessed_transaction.id,
            'original_amount': 1000,
            'discount_percent': 15,
            'source_card': cashback_card.id,
            'from_cashback': 0,
            "utc_offset_minutes": 0
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        client_status = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                      organization=self.organization)
        self.assertEqual(client_status.accrued_cashback, 150)

    def test_corporate_organization_cashback_uses_only_organizations_cashback_when_enough(self):
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=self.organization, card=None, accrued_cashback=500
        )

        partner_owner = UserFactory()

        partner_organization = OrganizationFactory(owner=partner_owner, cashback_group=None)
        PartnershipUtils.create_partnership_with_shared_cashback(org1=self.organization, org2=partner_organization)
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=partner_organization, card=None, accrued_cashback=300
        )

        data = {
            'transaction_id': self.unprocessed_transaction.id,
            'original_amount': 1000,
            'discount_percent': 0,
            'source_card': None,
            'from_cashback': 500,
            "utc_offset_minutes": 0
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        client_status = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                      organization=self.organization)
        self.assertEqual(client_status.accrued_cashback, 0)

        client_status_partner = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                              organization=partner_organization)
        self.assertEqual(client_status_partner.accrued_cashback, 300)

    def test_corporate_organization_cashback_uses_other_available_cashback_when_not_enough(self):
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=self.organization, card=None, accrued_cashback=500
        )

        partner_owner = UserFactory()

        partner_organization = OrganizationFactory(owner=partner_owner, cashback_group=None)
        PartnershipUtils.create_partnership_with_shared_cashback(org1=self.organization, org2=partner_organization)
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=partner_organization, card=None, accrued_cashback=300
        )

        data = {
            'transaction_id': self.unprocessed_transaction.id,
            'original_amount': 1000,
            'discount_percent': 0,
            'source_card': None,
            'from_cashback': 700,
            "utc_offset_minutes": 0
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        client_status = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                      organization=self.organization)
        self.assertEqual(client_status.accrued_cashback, 0)

        client_status_partner = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                              organization=partner_organization)
        self.assertEqual(client_status_partner.accrued_cashback, 100)

    def test_corporate_organization_cashback_must_take_from_organization_with_most_amount_first(self):
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=self.organization, card=None, accrued_cashback=500
        )

        partner_owner = UserFactory()

        partner_organization = OrganizationFactory(owner=partner_owner, cashback_group=None)
        PartnershipUtils.create_partnership_with_shared_cashback(org1=self.organization, org2=partner_organization)
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=partner_organization, card=None, accrued_cashback=300
        )

        bigger_organization = OrganizationFactory(owner=partner_owner, cashback_group=None)
        PartnershipUtils.create_partnership_with_shared_cashback(org1=self.organization, org2=bigger_organization)
        OrganizationClientFinancialStatusFactory(
            user=self.client_user, organization=bigger_organization, card=None, accrued_cashback=400
        )

        data = {
            'transaction_id': self.unprocessed_transaction.id,
            'original_amount': 1000,
            'discount_percent': 0,
            'source_card': None,
            'from_cashback': 1000,
            "utc_offset_minutes": 0
        }

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        client_status = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                      organization=self.organization)
        self.assertEqual(client_status.accrued_cashback, 0)

        client_status_partner = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                              organization=partner_organization)
        self.assertEqual(client_status_partner.accrued_cashback, 200)

        bigger_partner_status = OrganizationClientFinancialStatus.objects.get(user=self.client_user,
                                                                              organization=bigger_organization)
        self.assertEqual(bigger_partner_status.accrued_cashback, 0)
