from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.models import Service
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
        queryset = Service.objects.all()
        if country is not None:
            queryset = queryset.filter(subcategory__organizations__country=country).distinct()
        if city is not None:
            queryset = queryset.filter(subcategory__organizations__city=city).distinct()
        return queryset
