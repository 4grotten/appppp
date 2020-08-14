from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import PermissionDeniedException
from organizations.serializers.attendance_serializers import RecordAttendanceSerializer
from organizations.serializers.query_param_serializers import OrganizationUserQueryParamSerializer
from organizations.services.attendance_services import AttendanceService
from organizations.services.organization_services import OrganizationService
from users.serializers import AttendanceEmployeeSerializer


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
        serializer = RecordAttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_check_attendance(organization=organization, user=request.user):
            raise PermissionDeniedException('No rights to check attendance in this organization')

        user = serializer.validated_data['user']
        AttendanceService.record_arrival(employee=user, organization=organization, recorded_by=request.user)

        data = {'full_name': user.full_name}

        return Response(data)
