from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import Organization

from common.exceptions import NotAcceptableException
from common.serializers import CountryCityQueryParamSerializer
from organizations.serializers.query_param_serializers import OptionalOrganizationQueryParamSerializer
from shop.forms import ItemSubcategoryAdminForm
from shop.models import ItemCategory, ItemSubcategory, ShopItem
from shop.permissions import CanEditItemSubcategory
from shop.serializers.category_serializers import (
    ItemSubcategorySerializer, ItemSubcategoryCreateSerializer, ItemSubcategoryBriefSerializer, ItemCategorySerializer,
    ItemCategoryWithNonEmptySubcategoriesSerializer, ItemCategoryWithSubcategoriesSerializer,
    NonEmptyItemSubcategorySerializer
)
from shop.services.category_services import ItemSubcategoryService, ItemCategoryService
from utils.translator import GoogleTranslator


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
        partners = main_organization.requested_partnerships.filter(is_accepted=True).values_list('accepted_by', flat=True).distinct()
        partner_organizations = Organization.objects.filter(Q(id__in=partners) | Q(id=self.kwargs['pk']))
        item_categories = ShopItem.objects.filter(organization__in=partner_organizations, is_published=True, is_hidden=False).values_list('subcategory_id', flat=True).distinct()
        return ItemCategory.objects.filter(subcategories__in=item_categories).distinct().order_by('name')


class NonEmptyPartnerSubcategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = NonEmptyItemSubcategorySerializer

    def get_queryset(self):
        main_organization = Organization.objects.get(id=self.kwargs['pk'])
        partners = main_organization.requested_partnerships.filter(is_accepted=True).values_list('accepted_by', flat=True).distinct()
        partner_organizations = Organization.objects.filter(Q(id__in=partners) | Q(id=self.kwargs['pk']))
        category_id = self.request.query_params.get('category')
        shop_items = ShopItem.objects.filter(organization__in=partner_organizations).values_list('id', flat=True).distinct()
        return ItemSubcategory.objects.filter(category_id=category_id, id__in=shop_items).distinct().order_by('name')


class SubcategoryRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItemSubcategory)
    serializer_class = ItemSubcategorySerializer
    queryset = ItemSubcategory.objects.all()


class ItemSubcategoryCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemSubcategoryCreateSerializer
    queryset = ItemSubcategory.objects.all()

    
    def create(self, request, *args, **kwargs):
        serializer = ItemSubcategoryCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        name_ru = GoogleTranslator().translate(serializer.validated_data['name'], 'RU').text
        name_en = GoogleTranslator().translate(serializer.validated_data['name'], 'EN').text
        name_tr = GoogleTranslator().translate(serializer.validated_data['name'], 'TR').text
        subcategory = ItemSubcategory.objects.create(organization=serializer.validated_data['organization'],
                                       name=serializer.validated_data['name'],
                                       category=serializer.validated_data['category'],
                                       name_ru=name_ru,
                                       name_en=name_en,
                                       name_tr=name_tr)
        subcategory.save()
        return Response(self.serializer_class(subcategory).data, status=status.HTTP_201_CREATED)


class OrganizationSubcategoryListView(ListAPIView):
    serializer_class = ItemSubcategoryBriefSerializer
    pagination_class = None

    def get_queryset(self):
        return ItemSubcategoryService.get_orgs_nonempty_subcategories(organization_id=self.kwargs['pk'])
