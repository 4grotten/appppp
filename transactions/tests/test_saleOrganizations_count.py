from django.urls import reverse
from rest_framework.test import APITestCase

from common.tests.factories import CurrencyFactory
from organizations.tests.factories import (
    OrganizationFactory, RoleFactory, MembershipFactory
)
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class SaleOrganizationsTestCase(APITestCase):
    maxDiff = None

    def setUp(self):
        self.user = UserFactory(phone_number='+996555421221')
        self.user2 = UserFactory(phone_number='+996555421222')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}
        self.currency = CurrencyFactory(code='XXX')
        self.organization1 = OrganizationFactory(owner=self.user, currency=self.currency, cashback_group=None)
        self.organization2 = OrganizationFactory(owner=self.user2, currency=self.currency, cashback_group=None)

        self.role_admin_in_organization1 = RoleFactory(
            title='admin', organization=self.organization1, can_sale=True,
            can_check_attendance=True, can_see_stats=True, can_edit_organization=True,
            can_send_message=True, can_edit_partner=True)
        self.membership = MembershipFactory(organization=self.organization1, user=self.user2,
                                            role=self.role_admin_in_organization1)

        self.role_ne_admin_in_organization2 = RoleFactory(
            title='ne_admin', organization=self.organization2, can_sale=True,
            can_check_attendance=True, can_see_stats=False, can_edit_organization=True,
            can_send_message=True, can_edit_partner=True)
        self.membership = MembershipFactory(organization=self.organization2, user=self.user,
                                            role=self.role_ne_admin_in_organization2)

        self.client_user = UserFactory(phone_number='+996707909090')
        self.url = reverse('v1:sale_transaction_organizations')

    def test_accepted_get_sale_organizations_count(self):
        TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization1, currency=self.currency,
            original_amount=51.0, is_processed=False, status='rejected')
        TransactionFactory(
            client=self.client_user, organization=self.organization1, currency=self.currency,
            original_amount=52.0, is_processed=False, status='in_progress', type='online')
        TransactionFactory(
            client=self.client_user, organization=self.organization1, currency=self.currency,
            original_amount=52.0, is_processed=False, status='in_progress', type='offline')
        TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization1, currency=self.currency,
            original_amount=51.0, is_processed=True, status='accepted')
        TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization2, currency=self.currency,
            original_amount=51.0, is_processed=True, status='accepted')
        TransactionFactory(
            client=self.client_user, organization=self.organization2, currency=self.currency,
            original_amount=52.0, is_processed=False, status='in_progress', type='offline')
        response = self.client.get(self.url, **self.header, content_type='application/json')

        from_response_organization_2 = response.data.get('list')[0]
        from_response_organization_1 = response.data.get('list')[-1]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(from_response_organization_2.get('unprocessed_transaction_count'), 0)
        self.assertEqual(from_response_organization_1.get('unprocessed_transaction_count'), 1)
