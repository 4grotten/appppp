from common.exceptions import NotAcceptableException
from organizations.models import Organization, Attendance
from organizations.services.membership_services import MembershipService
from users.models import User


class AttendanceService:
    @classmethod
    def record_arrival(cls, employee: User, organization: Organization, recorded_by: User):
        if not MembershipService.is_organization_member(user=employee, organization=organization):
            raise NotAcceptableException('Given user is not a member of this organization')
        if cls.is_already_recorded(employee=employee, organization=organization):
            raise NotAcceptableException('This employee is already at work')

        Attendance.objects.create(user=employee, organization=organization, arrival_checked_by=recorded_by)

    @classmethod
    def is_already_recorded(cls, employee: User, organization: Organization):
        return Attendance.objects.filter(user=employee, organization=organization, is_active=True).exists()
