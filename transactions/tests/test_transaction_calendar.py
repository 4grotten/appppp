import json
from datetime import datetime

from django.urls import reverse
from rest_framework.test import APITestCase
from unittest import expectedFailure

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
        self.url = reverse('v1:org_client_calendar')
        self.user = UserFactory(phone_number='123456789')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}

        self.currency = CurrencyFactory(code='XXX')
        self.organization = OrganizationFactory(owner=self.user, currency=self.currency, cashback_group=None)

        self.client_user = UserFactory(phone_number='777777777')

        self.unprocessed_transaction = TransactionFactory(client=self.client_user, processed_by=self.user,
                                                          organization=self.organization, currency=self.currency)

    def test_accepted_get_calendar(self):
        processed_transaction_online = TransactionFactory(
            client=self.client_user, processed_by=self.user,
            is_processed=True, status='accepted', type='online',
            organization=self.organization, currency=self.currency,
            created_at=datetime(year=2021, month=2, day=7,
                                hour=12, minute=42, second=32)
        )
        processed_transaction_offline = TransactionFactory(client=self.client_user, processed_by=self.user,
                                                           is_processed=True, status='accepted', type='offline',
                                                           organization=self.organization, currency=self.currency)
        processed_transaction_unprocessed = TransactionFactory(client=self.client_user, processed_by=self.user,
                                                               is_processed=False, status='in_progress',
                                                               type='online',
                                                               organization=self.organization,
                                                               currency=self.currency)
