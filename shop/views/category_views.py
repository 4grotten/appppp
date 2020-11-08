from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.serializers.query_param_serializers import OptionalOrganizationQueryParamSerializer
from shop.models import ItemCategory, ItemSubcategory
from shop.permissions import CanEditItemSubcategory
from shop.serializers.category_serializers import (
    ItemCategoryWithSubcategoriesSerializer, ItemSubcategorySerializer, ItemSubcategoryCreateSerializer,
    ItemSubcategoryBriefSerializer, ItemCategorySerializer, ItemCategoryWithNonEmptySubcategoriesSerializer
)
from shop.services.category_services import ItemSubcategoryService, ItemCategoryService


class ItemCategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = ItemCategoryWithSubcategoriesSerializer
    queryset = ItemCategory.objects.all()

    def get_serializer_context(self):
        serializer = OptionalOrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        context = super().get_serializer_context()
        context['organization'] = serializer.validated_data['organization']
        return context


class ItemCategoryRetrieveView(RetrieveAPIView):
    permission_classes = ()
    serializer_class = ItemCategoryWithNonEmptySubcategoriesSerializer
    queryset = ItemCategory.objects.all()


class NonEmptyCategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        return ItemCategoryService.get_nonempty_general_categories()


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
