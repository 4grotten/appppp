import json
from datetime import datetime
from unittest.mock import patch, Mock

from django.urls import reverse
from rest_framework.test import APITestCase
from unittest import expectedFailure
from common.tests.factories import CurrencyFactory
from organizations.models import OrganizationClientFinancialStatus, DiscountCard
from organizations.tests.factories import (
    OrganizationFactory, OrganizationClientFinancialStatusFactory, DiscountCardFactory, RoleFactory, MembershipFactory
)
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class CompleteTransactionTestCase(APITestCase):
    maxDiff = None

    def setUp(self):
        self.user = UserFactory(phone_number='+996555421221')
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
        self.client_user = UserFactory(phone_number='+996707909090')
        self.client_user2 = UserFactory(phone_number='+996707777998')
        self.url = reverse('v1:organization_transactions')

    def test_get_accepted_data_with_processed_by_filter(self):
        transaction_offline = TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization, currency=self.currency,
            original_amount=51.0, is_processed=True, status='accepted')
        transaction_offline_rejected = TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization, currency=self.currency,
            original_amount=51.0, is_processed=False, status='rejected')
        transaction_offline_in_progress = TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization, currency=self.currency,
            original_amount=52.0, is_processed=False, status='in_progress')
        transaction_offline_processed_by_admin = TransactionFactory(
            client=self.client_user, processed_by=self.user_admin, organization=self.organization,
            currency=self.currency, original_amount=52.0, is_processed=True, status='accepted')
        transaction_offline_processed_by_admin = TransactionFactory(
            client=self.client_user, processed_by=self.user_admin, organization=self.organization,
            currency=self.currency, original_amount=52.0, is_processed=False, status='rejected')

        transaction_online = TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization, currency=self.currency,
            type='online', original_amount=51.0, is_processed=True, status='accepted')
        transaction_online_in_progress = TransactionFactory(
            client=self.client_user, processed_by=self.user, organization=self.organization, currency=self.currency,
            type='online', original_amount=51.0, is_processed=False, status='in_progress')
        transaction_online_processed_by_admin = TransactionFactory(
            client=self.client_user, processed_by=self.user_admin, organization=self.organization, type='online',
            currency=self.currency, original_amount=51.0, is_processed=True, status='accepted')

        url_parameters = {'organization': self.organization.id, 'processed_by': self.user.id}

        expected_data = {
            'total_count': 4,
            'total_pages': 1,
            'list': [
                {
                    "id": transaction_online_in_progress.pk, "currency": transaction_online_in_progress.currency.code,
                    "original_amount": float(transaction_online_in_progress.original_amount),
                    "discount_percent": transaction_online_in_progress.discount_percent,
                    "savings": float(transaction_online_in_progress.savings),
                    "from_cashback": float(transaction_online_in_progress.from_cashback),
                    "to_cashback": float(transaction_online_in_progress.to_cashback),
                    "final_amount": float(transaction_online_in_progress.final_amount),
                    "updated_at": transaction_online_in_progress.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "created_at": transaction_online_in_progress.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "type": transaction_online_in_progress.type,
                    "status": transaction_online_in_progress.status
                },
                {
                    "id": transaction_online.pk, "currency": transaction_online.currency.code,
                    "original_amount": float(transaction_online.original_amount),
                    "discount_percent": transaction_online.discount_percent,
                    "savings": float(transaction_online.savings),
                    "from_cashback": float(transaction_online.from_cashback),
                    "to_cashback": float(transaction_online.to_cashback),
                    "final_amount": float(transaction_online.final_amount),
                    "updated_at": transaction_online.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "created_at": transaction_online.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "type": transaction_online.type,
                    "status": transaction_online.status
                },
                {
                    "id": transaction_offline_rejected.pk, "currency": transaction_offline_rejected.currency.code,
                    "original_amount": float(transaction_offline_rejected.original_amount),
                    "discount_percent": transaction_offline_rejected.discount_percent,
                    "savings": float(transaction_offline_rejected.savings),
                    "from_cashback": float(transaction_offline_rejected.from_cashback),
                    "to_cashback": float(transaction_offline_rejected.to_cashback),
                    "final_amount": float(transaction_offline_rejected.final_amount),
                    "updated_at": transaction_offline_rejected.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "created_at": transaction_offline_rejected.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "type": transaction_offline_rejected.type,
                    "status": transaction_offline_rejected.status
                },
                {
                    "id": transaction_offline.pk, "currency": transaction_offline.currency.code,
                    "original_amount": float(transaction_offline.original_amount),
                    "discount_percent": transaction_offline.discount_percent,
                    "savings": float(transaction_offline.savings),
                    "from_cashback": float(transaction_offline.from_cashback),
                    "to_cashback": float(transaction_offline.to_cashback),
                    "final_amount": float(transaction_offline.final_amount),
                    "updated_at": transaction_offline.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "created_at": transaction_offline.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "type": transaction_offline.type,
                    "status": transaction_offline.status}]
        }

        response = self.client.get(self.url, url_parameters, **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)
