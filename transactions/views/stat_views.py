from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.services.organization_services import OrganizationService
from transactions.serializers.stats_serializers import StartEndDateSerializer, PartnersTotalStatsSerializer
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
                                                              start_day=serializer.validated_data['start'],
                                                              end_day=serializer.validated_data['end'],
                                                              currency=currency)
        data = PartnersTotalStatsSerializer(stats).data
        return Response(data)
