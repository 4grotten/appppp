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
        city = serializer.validated_data['city']

        organizations_in_country = Organization.objects.filter(country=country,
                                                               city=city).values_list('types', flat=True)
        queryset = Service.objects.filter(subcategory__in=organizations_in_country).distinct()
        return queryset
