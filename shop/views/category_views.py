from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from organizations.models import Organization

from common.exceptions import NotAcceptableException
from common.serializers import CountryCityQueryParamSerializer
from organizations.serializers.query_param_serializers import OptionalOrganizationQueryParamSerializer
from shop.models import ItemCategory, ItemSubcategory, ShopItem
from shop.permissions import CanEditItemSubcategory
from shop.serializers.category_serializers import (
    ItemSubcategorySerializer, ItemSubcategoryCreateSerializer, ItemSubcategoryBriefSerializer, ItemCategorySerializer,
    ItemCategoryWithNonEmptySubcategoriesSerializer, ItemCategoryWithSubcategoriesSerializer,
    NonEmptyItemSubcategorySerializer
)
from shop.services.category_services import ItemSubcategoryService, ItemCategoryService


# ToDo: write tests for this view
class ItemCategoryAllSubcategoriesView(RetrieveAPIView):
    permission_classes = ()
    serializer_class = ItemCategoryWithSubcategoriesSerializer
    queryset = ItemCategory.objects.all()

    def get_serializer_context(self):
        serializer = OptionalOrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid organization is required in query parameters'))

        context = super().get_serializer_context()
        context['organization'] = serializer.validated_data['organization']

        return context


class ItemCategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = ItemCategorySerializer
    queryset = ItemCategory.objects.all()


class ItemCategoryRetrieveView(RetrieveAPIView):
    permission_classes = ()
    serializer_class = ItemCategoryWithNonEmptySubcategoriesSerializer
    queryset = ItemCategory.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        qp_serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not qp_serializer.is_valid():
            raise NotAcceptableException(_('Valid country and city are required in query parameters'))

        context['city'] = qp_serializer.validated_data['city']
        context['country'] = qp_serializer.validated_data['country']

        return context


class NonEmptyCategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        qp_serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not qp_serializer.is_valid():
            raise NotAcceptableException(_('Valid country and city are required in query parameters'))

        return ItemCategoryService.get_nonempty_general_categories(country=qp_serializer.validated_data['country'],
                                                                   city=qp_serializer.validated_data['city'])


class NonEmptyPartnerCategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        main_organization = Organization.objects.get(id=self.kwargs['pk'])
        org_partners = Organization.objects.filter(
            types__organizations__in=main_organization.requested_partnerships.filter(is_accepted=True).values_list(
                'accepted_by', flat=True)).annotate(
            orgs_count=Count('types__organizations', distinct=True)).distinct().order_by('-orgs_count')

        return ItemCategory.objects.filter(subcategories__organization_id__in=org_partners).distinct().order_by('name')


class NonEmptyPartnerSubcategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = NonEmptyItemSubcategorySerializer

    def get_queryset(self):
        main_organization = Organization.objects.get(id=self.kwargs['pk'])
        org_partners = Organization.objects.filter(
            types__organizations__in=main_organization.requested_partnerships.filter(is_accepted=True).values_list(
                'accepted_by', flat=True)).annotate(
            orgs_count=Count('types__organizations', distinct=True)).distinct().order_by('-orgs_count')
        category_id = self.request.query_params.get('category')
        return ItemSubcategory.objects.filter(category_id=category_id, organization_id__in=org_partners).distinct().order_by('name')


class SubcategoryRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItemSubcategory)
    serializer_class = ItemSubcategorySerializer
    queryset = ItemSubcategory.objects.all()


class ItemSubcategoryCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemSubcategoryCreateSerializer
    queryset = ItemSubcategory.objects.all()


class OrganizationSubcategoryListView(ListAPIView):
    serializer_class = ItemSubcategoryBriefSerializer
    pagination_class = None

    def get_queryset(self):
        return ItemSubcategoryService.get_orgs_nonempty_subcategories(organization_id=self.kwargs['pk'])
