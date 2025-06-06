from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from django.db.models import Q

from common.exceptions import NotAcceptableException
from common.serializers import ServiceCountryCityQueryParamSerializer
from organizations.models import Service, Organization
from organizations.serializers.query_param_serializers import OrganizationCoutrySerializer
from organizations.serializers.service_serializers import ServiceSerializer
from shop.serializers.category_serializers import ItemSubcategorySerializer
from shop.services.category_services import ItemCategoryService


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

        organizations = Organization.objects.filter(
            shop_items__price__isnull=False,
            has_delivery=True,
            is_active=True,
            shop_items__isnull=False
        ).exclude(is_banned=True).exclude(is_deleted=True).distinct()

        if country is not None:
            organizations = organizations.filter(country=country)
        if city is not None:
            organizations = organizations.filter(city=city)

        queryset = Service.objects.filter(
            Q(subcategory__organizations__in=organizations, is_active=True) |
            Q(is_entertainment=True) |
            Q(is_resume=True) |
            Q(is_wholesale=True) |
            Q(is_application=True)
        ).distinct()

        return queryset.order_by('-is_discounts', 'ordering')


class NonEmptyServiceCategoryItemListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = ItemSubcategorySerializer

    def get_queryset(self):
        qp_serializer = ServiceCountryCityQueryParamSerializer(data=self.request.GET)
        if not qp_serializer.is_valid():
            raise NotAcceptableException(_('Valid service, country and city are required in query parameters'))
        return ItemCategoryService.get_nonempty_general_service_categories(
            service=self.kwargs['pk'], country=qp_serializer.validated_data['country'],
            city=qp_serializer.validated_data['city'])
