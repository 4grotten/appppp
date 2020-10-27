from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.serializers.query_param_serializers import OptionalOrganizationQueryParamSerializer
from shop.models import ItemCategory, ItemSubcategory
from shop.permissions import CanEditItemSubcategory
from shop.serializers.category_serializers import (
    ItemCategorySerializer, ItemSubcategorySerializer, ItemSubcategoryCreateSerializer, ItemSubcategoryBriefSerializer
)
from shop.services.category_services import ItemSubcategoryService


class ItemCategoriesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = ItemCategorySerializer
    queryset = ItemCategory.objects.all()

    def get_serializer_context(self):
        serializer = OptionalOrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        context = super().get_serializer_context()
        context['organization'] = serializer.validated_data['organization']
        return context


class ItemCategoryRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItemSubcategory)
    serializer_class = ItemSubcategorySerializer
    queryset = ItemSubcategory.objects.all()


class ItemCategoriesCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemSubcategoryCreateSerializer
    queryset = ItemSubcategory.objects.all()


class OrganizationSubcategoriesView(ListAPIView):
    serializer_class = ItemSubcategoryBriefSerializer

    def get_queryset(self):
        return ItemSubcategoryService.get_nonempty_subcategories(organization_id=self.kwargs['pk'])
