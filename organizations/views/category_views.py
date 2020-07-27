from rest_framework.generics import ListAPIView, RetrieveAPIView

from organizations.serializers.categories_serializers import OrganizationDetailSerializer
from organizations.services.categories_services import OrganizationCategoryService


class CategoryDetailAPIView(RetrieveAPIView):
    serializer_class = OrganizationDetailSerializer
    queryset = OrganizationCategoryService.filter()
