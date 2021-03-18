from django.conf import settings
from django.utils.timezone import now
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException, PermissionDeniedException
from organizations.services.organization_services import OrganizationService
from transactions.serializers.stats_serializers import (
    StartEndDateSerializer, TotalStatsSerializer, StartEndProcessedByQueryParamSerializer,
    OrganizationCalendarSerializer, CalendarClientSerializer
)
from transactions.services.stats_services import StatisticsService


class PartnersTotalStatsView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(id=kwargs['pk'])
        currency = request.META.get('HTTP_CURRENCY', settings.APP_BASE_CURRENCY)
        stats = StatisticsService.get_total_stats_of_partners(organization=organization, requesting_user=request.user,
                                                              start_date=serializer.validated_data['start'],
                                                              end_date=serializer.validated_data['end'],
                                                              currency=currency)
        data = TotalStatsSerializer(stats).data
        return Response(data)


class OrganizationTotalsView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        serializer = StartEndProcessedByQueryParamSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(id=kwargs['pk'])
        if not OrganizationService.user_can_see_stats(organization=organization, user=request.user):
            raise NotAcceptableException('No rights to see stats of organization')

        stats = StatisticsService.get_totals_of_organization(organization=organization,
                                                             start_date=serializer.validated_data['start'],
                                                             end_date=serializer.validated_data['end'],
                                                             processed_by=serializer.validated_data['processed_by'],
                                                             client=serializer.validated_data['client'])
        data = TotalStatsSerializer(stats).data
        return Response(data)


class OrganizationTransactionCalendarView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = OrganizationCalendarSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_see_stats(organization=organization, user=request.user):
            raise PermissionDeniedException('No rights to check attendance in this organization')

        month_year = serializer.validated_data['month_year']
        if month_year is None:
            month_year = now().date()

        data = CalendarClientSerializer(serializer.validated_data['client'],
                                        context={'organization': organization, 'request': request,
                                                 'month_year': month_year,
                                                 'client': serializer.validated_data['client'],
                                                 }).data
        return Response(data)
