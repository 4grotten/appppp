import json
import re

from django.urls import reverse
from rest_framework.test import APITestCase
from unittest import expectedFailure

from common.tests.factories import CurrencyFactory
from organizations.models import OrganizationClientFinancialStatus, DiscountCard
from organizations.tests.factories import (
    OrganizationFactory, OrganizationClientFinancialStatusFactory, DiscountCardFactory, RoleFactory, MembershipFactory
)
from organizations.tests.test_utils import PartnershipUtils
from transactions.models import Transaction
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class DeclineTransactionTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory(phone_number='123456789', full_name='Owner')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}

        self.currency = CurrencyFactory(code='XXX')
        self.organization = OrganizationFactory(owner=self.user, currency=self.currency, cashback_group=None)

        self.role_admin = RoleFactory(
            title='admin', organization=self.organization, can_sale=True,
            can_check_attendance=True, can_see_stats=True, can_edit_organization=True,
            can_send_message=True, can_edit_partner=True)
        self.user_admin = UserFactory(phone_number='+996777009900')
        self.membership = MembershipFactory(organization=self.organization, user=self.user_admin, role=self.role_admin)

        self.client_user = UserFactory(phone_number='777777777')

    def test_accepted_transaction_decline(self):
        transaction_offline = TransactionFactory(client=self.client_user, processed_by=self.user_admin,
                                                 organization=self.organization, currency=self.currency,
                                                 is_processed=True, status='accepted')
        response = self.client.delete(
            reverse('v1:organization_transaction_detail', kwargs={"pk": int(transaction_offline.id)}), **self.header,
            content_type='application/json')
        self.assertEqual(response.status_code, 204)
        changed_transaction = Transaction.objects.get(id=transaction_offline.id)

        self.assertEqual(changed_transaction.id, transaction_offline.id)
        self.assertFalse(changed_transaction.is_processed)
        self.assertEqual(changed_transaction.type, 'offline')
        self.assertEqual(changed_transaction.status, 'rejected')
        self.assertEqual(changed_transaction.processed_by, self.user)
        self.assertEqual(changed_transaction.employee_name, self.user.full_name)
        self.assertEqual(changed_transaction.employee_role, 'Owner')
        self.assertEqual(changed_transaction.employee_avatar, self.user.avatar)

    def test_fail_on_two_time_reject_transaction_decline(self):
        transaction_offline = TransactionFactory(client=self.client_user, processed_by=self.user_admin,
                                                 organization=self.organization, currency=self.currency,
                                                 is_processed=False, status='rejected')
        response = self.client.delete(
            reverse('v1:organization_transaction_detail', kwargs={"pk": int(transaction_offline.id)}), **self.header,
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_fail_on_permissions(self):
        transaction_offline = TransactionFactory(client=self.client_user, processed_by=self.user_admin,
                                                 organization=self.organization, currency=self.currency,
                                                 is_processed=True, status='accepted')
        role_security = RoleFactory(
            title='admin', organization=self.organization, can_sale=True,
            can_check_attendance=True, can_see_stats=False, can_edit_organization=True,
            can_send_message=True, can_edit_partner=True)
        user_security = UserFactory(phone_number='+996777009977')
        membership = MembershipFactory(organization=self.organization, user=user_security,
                                       role=role_security)
        token = TokenFactory(user=user_security)
        header = {"HTTP_AUTHORIZATION": f"Token {token}"}

        response = self.client.delete(
            reverse('v1:organization_transaction_detail', kwargs={"pk": int(transaction_offline.id)}), **header,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
