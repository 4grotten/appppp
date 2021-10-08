from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets

from common.exceptions import NotAcceptableException
from organizations.models import Service, Organization
from organizations.serializers.query_param_serializers import OrganizationCoutrySerializer
from organizations.serializers.service_serializers import ServiceSerializer


class ServiceReadOnlySet(viewsets.ReadOnlyModelViewSet):
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

        organizations = Organization.objects.filter(shop_items__price__isnull=False, has_delivery=True, is_active=True,
                                                    shop_items__isnull=False).exclude(is_banned=True).\
            exclude(is_deleted=True).distinct()
        if country is not None:
            organizations = organizations.filter(country=country)
        if city is not None:
            organizations = organizations.filter(city=city)
        queryset = Service.objects.filter(subcategory__organizations__in=organizations).distinct()
        return queryset
