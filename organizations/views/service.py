from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.models import Service, Organization
from organizations.serializers.query_param_serializers import OrganizationCoutrySerializer
from organizations.serializers.service_serializers import ServiceSerializer


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

        queryset = Organization.objects.all()
        print(queryset.count())
        if country is not None:
            queryset = queryset.filter(country=country)
        if city is not None:
            queryset = queryset.filter(city=city)
        print(queryset.count())
        organizations_in_country = queryset.values_list('types', flat=True).distinct()
        print(organizations_in_country)
        services = Service.objects.filter(subcategory__in=organizations_in_country).distinct()
        return services
