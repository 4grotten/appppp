import os
from datetime import datetime

from django.urls import reverse
from rest_framework.test import APITestCase

from common.tests.factories import CurrencyFactory
from organizations.tests.factories import OrganizationFactory
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class CompleteTransactionTestCase(APITestCase):
    maxDiff = None

    def setUp(self):
        self.user = UserFactory(phone_number='123456789')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}

        self.currency = CurrencyFactory(code='XXX')
        self.organization = OrganizationFactory(owner=self.user, currency=self.currency, cashback_group=None)

        self.client_user = UserFactory(phone_number='777777777')

        self.unprocessed_transaction = TransactionFactory(client=self.client_user, processed_by=self.user,
                                                          organization=self.organization, currency=self.currency)
        self.url = reverse('v1:org_client_calendar')

    def test_accepted_get_calendar(self):
        url_parameters = {'client': self.client_user.id, 'organization': self.organization.id, 'month_year': '2021-02'}

        display_time = datetime(2021, 2, 3, 11, 15, 0)

        processed_transaction_online = TransactionFactory(
            client=self.client_user, processed_by=self.user,
            is_processed=True, status='accepted', type='online',
            organization=self.organization, currency=self.currency,
            display_time=display_time,
        )

        processed_transaction_online_at_same_day = TransactionFactory(
            client=self.client_user, processed_by=self.user,
            is_processed=True, status='accepted', type='online',
            organization=self.organization, currency=self.currency,
            display_time=display_time,
        )

        display_time = datetime(2021, 2, 5, 11, 15, 0)

        processed_transaction_offline = TransactionFactory(
            client=self.client_user, processed_by=self.user,
            is_processed=True, status='accepted', type='offline',
            organization=self.organization, currency=self.currency,
            display_time=display_time,
        )

        display_time = datetime(2021, 2, 6, 11, 15, 0)

        processed_transaction_unprocessed = TransactionFactory(
            client=self.client_user, processed_by=self.user,
            is_processed=False, status='in_progress',
            type='online',
            organization=self.organization, currency=self.currency,
            display_time=display_time,
        )
        display_time = datetime(2021, 2, 7, 11, 15, 0)

        processed_transaction_unprocessed = TransactionFactory(
            client=self.client_user, processed_by=self.user,
            is_processed=False, status='in_progress',
            type='offline',
            organization=self.organization, currency=self.currency,
            display_time=display_time,
        )
        expected_data = {"client": {"id": self.client_user.id, "full_name": self.client_user.full_name,
                                    "avatar":
                                        {
                                            "id": self.client_user.avatar.id,
                                            "file": f"http://testserver{self.client_user.avatar.file.url}",
                                            "name": os.path.basename(self.client_user.avatar.file.name),
                                            "large": f"http://testserver{self.client_user.avatar.large.url}",
                                            "medium": f"http://testserver{self.client_user.avatar.medium.url}",
                                            "small": f"http://testserver{self.client_user.avatar.small.url}",
                                        },
                                    "role": "Client"},
                         "calendar": ["2021-02-06", "2021-02-05", "2021-02-03"]}
        response = self.client.get(self.url, url_parameters, **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_serializer_fail_on_client_get_calendar(self):
        url_parameters = {'organization': self.organization.id, }
        response = self.client.get(self.url, url_parameters, **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 406)

    def test_serializer_fail_on_organization_get_calendar(self):
        url_parameters = {'client': self.client_user.id, }
        response = self.client.get(self.url, url_parameters, **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 406)

    def test_serializer_fail_on_month_year_get_calendar(self):
        url_parameters = {'client': self.client_user.id, 'month_year': '02-2002',
                          'organization': self.organization.id, }
        response = self.client.get(self.url, url_parameters, **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 406)

    def test_with_no_month_year_get_calendar(self):
        url_parameters = {'client': self.client_user.id, 'organization': self.organization.id}
        response = self.client.get(self.url, url_parameters, **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_failed_no_permission(self):
        user = UserFactory(phone_number='123456769')
        url_parameters = {'client': self.client_user.id, 'organization': self.organization.id}
        token = TokenFactory(user=user)
        header = {"HTTP_AUTHORIZATION": f"Token {token}"}
        response = self.client.get(self.url, url_parameters, **header, content_type='application/json')
        self.assertEqual(response.status_code, 403)
