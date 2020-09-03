from django.utils.timezone import now
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import PermissionDeniedException
from organizations.serializers.attendance_serializers import (
    CreateAttendanceSerializer, GroupAttendanceSerializer,
    GlobalAttendanceSerializer)
from organizations.serializers.query_param_serializers import (
    OrganizationUserQueryParamSerializer, MonthYearQueryParamSerializer
)
from organizations.services.attendance_services import AttendanceService
from organizations.services.membership_services import MembershipService
from organizations.services.organization_services import OrganizationService
from users.serializers import AttendanceEmployeeSerializer, EmployeeWithRoleSerializer


class AttendanceUserInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = OrganizationUserQueryParamSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']

        if not OrganizationService.user_can_check_attendance(organization=organization, user=request.user):
            raise PermissionDeniedException('No rights to check attendance in this organization')

        data = AttendanceEmployeeSerializer(serializer.validated_data['user'],
                                            context={'organization': organization}).data
        return Response(data)


class AttendanceView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = CreateAttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_check_attendance(organization=organization, user=request.user):
            raise PermissionDeniedException('No rights to check attendance in this organization')

        user = serializer.validated_data['user']
        is_active = AttendanceService.record_arrival(employee=user, organization=organization, recorded_by=request.user)

        data = {
            'full_name': user.full_name,
            'is_active': is_active
        }

        return Response(data)


class AttendanceStatsView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, *args, **kwargs):
        serializer = MonthYearQueryParamSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        membership = MembershipService.get(id=pk)

        organization = membership.organization
        if not OrganizationService.user_can_check_attendance(organization=organization, user=request.user):
            raise PermissionDeniedException('No rights to check attendance in this organization')

        month_year = serializer.validated_data['month_year']
        if month_year is None:
            month_year = now().date()

        grouped_attendances = AttendanceService.get_grouped_monthly_attendances(
            employee=membership.user, organization=organization, month_year=month_year
        )

        employee = EmployeeWithRoleSerializer(membership.user, context={'organization': organization}).data

        data = {
            'employee': employee,
            'hired_date': membership.created_at,
            'calendar': GroupAttendanceSerializer(grouped_attendances, many=True).data
        }
        return Response(data)


class GlobalAttendanceView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = GlobalAttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = serializer.validated_data['user']
        organization = OrganizationService.get_first_organization_of_user(user=user)

        if not OrganizationService.user_can_check_attendance(organization=organization, user=request.user):
            raise PermissionDeniedException('No rights to check attendance in this organization')

        is_active = AttendanceService.record_arrival(employee=user, organization=organization, recorded_by=request.user)

        data = {
            'full_name': user.full_name,
            'is_active': is_active
        }

        return Response(data)
