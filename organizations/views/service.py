from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.models import Service, Organization
from organizations.serializers.query_param_serializers import OrganizationCoutrySerializer
from organizations.serializers.service_serializers import ServiceSerializer
from organizations.services.organization_services import OrganizationService


class ServiceReadOnlySet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    pagination_class = None

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _('Valid country and city are required in query parameters'))

        country = serializer.validated_data['country']
        print(country)
        city = serializer.validated_data['city']

        organizations = Organization.objects.all()
        organizations_in_country = OrganizationService._filter_by_country_and_city(queryset=organizations, country=country, city=city).distinct().values_list('types', flat=True)
        print(organizations_in_country)
        services = Service.objects.filter(subcategory__in=organizations_in_country).distinct()
        return services
