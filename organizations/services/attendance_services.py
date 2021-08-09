from datetime import timedelta
from itertools import groupby
from typing import Union

from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException
from notifications.constants import (
    NOTIFICATION_MODE_PERSONAL, ATTENDANCE_IN, ATTENDANCE_IN_TITLE, ATTENDANCE_DESCRIPTION, CHECK_ATTENDANCE_IN,
    CHECK_ATTENDANCE_IN_TITLE, ATTENDANCE_OUT, ATTENDANCE_OUT_TITLE, CHECK_ATTENDANCE_OUT, CHECK_ATTENDANCE_OUT_TITLE
)
from notifications.tasks import sent_notification
from organizations.models import Organization, Attendance, Partnership, Membership
from organizations.services.membership_services import MembershipService
from organizations.services.organization_services import OrganizationService
from users.models import User


class AttendanceService:
    @classmethod
    def _auto_depart_by_system(cls, employee: User, organization: Organization):
        today = now().date()
        unclosed_past_attendances = Attendance.objects.filter(
            user=employee, organization=organization, is_active=True).filter(arrival_time__lt=today)
        # ToDo: look for bulk update methods
        for attendance in unclosed_past_attendances:
            attendance.departure_time = attendance.arrival_time.replace(hour=organization.closes_at.hour,
                                                                        minute=organization.closes_at.minute,
                                                                        second=0)
            if attendance.departure_time < attendance.arrival_time:
                attendance.departure_time = attendance.departure_time + timedelta(days=1)
            attendance.is_active = False
            attendance.departure_checker_role = None
            attendance.save()

    @classmethod
    def record_arrival(cls, employee: User, organization: Organization, recorded_by: User, checker_role=None) -> bool:
        """
        returns is_active status of attendance
        """
        cls._auto_depart_by_system(employee=employee, organization=organization)

        if not MembershipService.is_organization_member(user=employee, organization=organization):
            raise NotAcceptableException(_('Given user is not a member of this organization'))

        # ToDo search why this code is needed
        if not checker_role:
            role = OrganizationService.get_user_role_in_organization(organization=organization, user=recorded_by)
        else:
            role = checker_role

        rows = Attendance.objects.filter(
            user=employee, organization=organization, is_active=True).update(
            is_active=False, departure_time=now(), departure_checked_by=recorded_by, departure_checker_role=role)
        membership = Membership.objects.get(organization=organization, user=employee)
        if rows < 1:
            Attendance.objects.create(user=employee, organization=organization, arrival_checked_by=recorded_by,
                                      arrival_checker_role=role)
            sent_notification.delay(
                recipient_id=employee.id,
                sender_id=recorded_by.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=ATTENDANCE_IN,
                title=ATTENDANCE_IN_TITLE.format(organization=organization.title),
                description=ATTENDANCE_DESCRIPTION,
                organization_id=organization.id,
                extra_data=dict(role=role, employee_id=membership.id, organization=organization.title)
            )
            sent_notification.delay(
                recipient_id=recorded_by.id,
                sender_id=employee.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=CHECK_ATTENDANCE_IN,
                title=CHECK_ATTENDANCE_IN_TITLE.format(organization=organization.title),
                description=ATTENDANCE_DESCRIPTION,
                organization_id=organization.id,
                extra_data=dict(employee_id=membership.id, organization=organization.title)
            )
            return True
        sent_notification.delay(
            recipient_id=employee.id,
            sender_id=recorded_by.id,
            mode=NOTIFICATION_MODE_PERSONAL,
            notification_type=ATTENDANCE_OUT,
            title=ATTENDANCE_OUT_TITLE.format(organization=organization.title),
            description=ATTENDANCE_DESCRIPTION,
            organization_id=organization.id,
            extra_data=dict(role=role, employee_id=membership.id, organization=organization.title)
        )
        sent_notification.delay(
            recipient_id=recorded_by.id,
            sender_id=employee.id,
            mode=NOTIFICATION_MODE_PERSONAL,
            notification_type=CHECK_ATTENDANCE_OUT,
            title=CHECK_ATTENDANCE_OUT_TITLE.format(organization=organization.title),
            description=ATTENDANCE_DESCRIPTION,
            organization_id=organization.id,
            extra_data=dict(employee_id=membership.id, organization=organization.title)
        )
        return False

    @classmethod
    def get_user_organizations_associated_with_checker(cls, user: User, recorded_by: User):
        rows = []
        organizations = Organization.objects.filter(memberships__user=user)
        recorded_by_organizations = Organization.objects.filter(memberships__user=recorded_by)

        for organization in organizations:
            for rec_organization in recorded_by_organizations:
                if Partnership.objects.filter(
                        Q(accepted_by=organization, requested_by=rec_organization) |
                        Q(accepted_by=rec_organization, requested_by=organization), is_accepted=True
                ).exists():
                    partnership1 = Partnership.objects.get(accepted_by=organization, requested_by=rec_organization)
                    partnership2 = Partnership.objects.get(accepted_by=rec_organization, requested_by=organization)

                    if partnership1.can_check_attendance or partnership2.can_check_attendance:
                        if OrganizationService.user_can_check_attendance(organization=organization,
                                                                         user=recorded_by):
                            rows.append(organization.id)

        return Organization.objects.filter(id__in=rows)

    @classmethod
    def is_checked_in(cls, employee: User, organization: Organization):
        cls._auto_depart_by_system(employee=employee, organization=organization)
        return Attendance.objects.filter(user=employee, organization=organization, is_active=True).exists()

    @staticmethod
    def _extract_date(attendance: Attendance):
        return attendance.arrival_time.date()

    @classmethod
    def get_grouped_monthly_attendances(cls, employee: User, organization: Organization, month_year) -> list:
        cls._auto_depart_by_system(employee=employee, organization=organization)

        attendances = Attendance.objects.filter(user=employee, organization=organization).filter(
            arrival_time__year=month_year.year).filter(arrival_time__month=month_year.month).order_by('arrival_time')

        result = []
        for day, group in groupby(attendances, key=cls._extract_date):
            day_str = day.strftime('%Y-%m-%d')
            date = {
                'date': day_str,
                'attendances': list(group)
            }
            result.append(date)

        return result

    @classmethod
    def get_latest_attendance(cls, employee: User, organization: Organization) -> Union[Attendance, None]:
        return Attendance.objects.filter(user=employee, organization=organization).order_by('-arrival_time').first()
