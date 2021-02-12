import json

from django.urls import reverse
from rest_framework.test import APITestCase
from unittest import expectedFailure
from unittest.mock import patch, Mock, call

from common.tests.factories import CurrencyFactory
from organizations.models import OrganizationClientFinancialStatus, DiscountCard
from organizations.tests.factories import (
    OrganizationFactory, OrganizationClientFinancialStatusFactory, DiscountCardFactory, MembershipFactory, RoleFactory
)
from organizations.tests.test_utils import PartnershipUtils
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class UserAttendanceInfo(APITestCase):
    def setUp(self):
        self.url = reverse('v1:record_arrival')
        self.user_owner = UserFactory(phone_number='123456789')
        self.user_employee = UserFactory(phone_number='123456783')
        self.user_not_employee = UserFactory(phone_number='123434783')
        self.user_employee_with_no_permission = UserFactory(phone_number='123456755')
        self.role = RoleFactory(can_check_attendance=False)
        self.token = TokenFactory(user=self.user_owner)
        self.token_with_no_permission = TokenFactory(user=self.user_employee_with_no_permission)
        self.header_with_no_permission = {"HTTP_AUTHORIZATION": f"Token {self.token_with_no_permission}"}
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}
        self.organization = OrganizationFactory(owner=self.user_owner)
        self.membership = MembershipFactory(organization=self.organization, user=self.user_employee)
        self.membership_with_no_permission = MembershipFactory(organization=self.organization, user=self.user_employee_with_no_permission,
                                            role=self.role)

    @patch('notifications.tasks.sent_notification.delay')
    def test_accept_attendance(self, notification: Mock):
        data = {
            'user': self.user_employee.id,
            'organization': self.organization.id
        }
        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('is_active'))

        notification.assert_has_calls([
            call(description=' ',
                 extra_data={'role': 'Owner', 'employee_id': self.membership.id,
                             'organization': self.organization.title},
                 mode='personal', notification_type='attendance_in', organization_id=self.organization.id,
                 recipient_id=self.user_employee.id, sender_id=self.user_owner.id,
                 title=f'Input {self.organization.title}'),
            call(description=' ',
                 extra_data={'employee_id': self.membership.id, 'organization': self.organization.title},
                 mode='personal',
                 notification_type='check_attendance_in', organization_id=self.organization.id,
                 recipient_id=self.user_owner.id, sender_id=self.user_employee.id,
                 title=f'Entry pass {self.organization.title}')
        ])

    @patch('notifications.tasks.sent_notification.delay')
    def test_accept_out_attendance(self, notification: Mock):
        data = {
            'user': self.user_employee.id,
            'organization': self.organization.id
        }
        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('is_active'))

        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data.get('is_active'))
        notification.assert_has_calls([
            call(description=' ',
                 extra_data={'role': 'Owner', 'employee_id': self.membership.id,
                             'organization': self.organization.title},
                 mode='personal', notification_type='attendance_in', organization_id=self.organization.id,
                 recipient_id=self.user_employee.id, sender_id=self.user_owner.id,
                 title=f'Input {self.organization.title}'),
            call(description=' ',
                 extra_data={'employee_id': self.membership.id, 'organization': self.organization.title},
                 mode='personal',
                 notification_type='check_attendance_in', organization_id=self.organization.id,
                 recipient_id=self.user_owner.id, sender_id=self.user_employee.id,
                 title=f'Entry pass {self.organization.title}'),
            call(description=' ', extra_data={'role': 'Owner', 'employee_id': self.membership.id,
                                              'organization': self.organization.title},
                 mode='personal', notification_type='attendance_out', organization_id=self.organization.id,
                 recipient_id=self.user_employee.id, sender_id=self.user_owner.id,
                 title=f'Exit {self.organization.title}'),
            call(description=' ',
                 extra_data={'employee_id': self.membership.id, 'organization': self.organization.title},
                 mode='personal',
                 notification_type='check_attendance_out', organization_id=self.organization.id,
                 recipient_id=self.user_owner.id, sender_id=self.user_employee.id,
                 title=f'Exit pass {self.organization.title}'),

        ])

    def test_serializer_failed_attendance(self):
        data = {
            'user': 'sad',
            'organization': self.organization.id
        }
        response = self.client.post(self.url, data=json.dumps(data), **self.header, content_type='application/json')
        self.assertEqual(response.status_code, 406)

    def test_permission_failed_attendance(self):
        data = {
            'user': self.user_employee.id,
            'organization': self.organization.id
        }
        response = self.client.post(self.url, data=json.dumps(data), **self.header_with_no_permission,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_failed_not_employee_attendance(self):
        data = {
            'user': self.user_not_employee.id,
            'organization': self.organization.id
        }
        response = self.client.post(self.url, data=json.dumps(data), **self.header,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 406)
