from itertools import groupby
from typing import Union

from django.utils.timezone import now

from common.exceptions import NotAcceptableException
from organizations.models import Organization, Attendance
from organizations.services.membership_services import MembershipService
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
            attendance.is_active = False
            attendance.save()

    @classmethod
    def record_arrival(cls, employee: User, organization: Organization, recorded_by: User) -> bool:
        """
        returns true if employee is checking in, false when checking out
        """
        cls._auto_depart_by_system(employee=employee, organization=organization)

        if not MembershipService.is_organization_member(user=employee, organization=organization):
            raise NotAcceptableException('Given user is not a member of this organization')

        rows = Attendance.objects.filter(
            user=employee, organization=organization, is_active=True).update(
            is_active=False, departure_time=now(), departure_checked_by=recorded_by)
        if rows < 1:
            Attendance.objects.create(user=employee, organization=organization, arrival_checked_by=recorded_by)
            return True
        return False

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
