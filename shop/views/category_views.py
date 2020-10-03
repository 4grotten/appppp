from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.serializers.query_param_serializers import OptionalOrganizationQueryParamSerializer
from shop.models import MainCategory, ItemCategory
from shop.permissions import CanEditItemCategory
from shop.serializers.category_serializers import (
    MainCategorySerializer, ItemCategorySerializer, ItemCategoryCreateSerializer
)


class ItemCategoriesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = MainCategorySerializer
    queryset = MainCategory.objects.all()

    def get_serializer_context(self):
        serializer = OptionalOrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        context = super().get_serializer_context()
        context['organization'] = serializer.validated_data['organization']
        return context


class ItemCategoryRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItemCategory)
    serializer_class = ItemCategorySerializer
    queryset = ItemCategory.objects.all()


class ItemCategoriesCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCategoryCreateSerializer
    queryset = ItemCategory.objects.all()
