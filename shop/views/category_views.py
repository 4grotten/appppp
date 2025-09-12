from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import Organization

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.serializers import CountryCityQueryParamSerializer
from organizations.serializers.query_param_serializers import (
    OptionalOrganizationQueryParamSerializer,
)
from shop.forms import ItemSubcategoryAdminForm
from shop.models import ItemCategory, ItemSubcategory, ShopItem
from shop.permissions import CanEditItemSubcategory
from shop.serializers.category_serializers import (
    ItemSubcategorySerializer,
    ItemSubcategoryCreateSerializer,
    ItemSubcategoryBriefSerializer,
    ItemCategorySerializer,
    ItemCategoryWithNonEmptySubcategoriesSerializer,
    ItemCategoryWithSubcategoriesSerializer,
    NonEmptyItemSubcategorySerializer,
)
from shop.services.category_services import ItemSubcategoryService, ItemCategoryService
from utils.translator import GoogleTranslator, GPTTranslator


# ToDo: write tests for this view
class ItemCategoryAllSubcategoriesView(RetrieveAPIView):
    permission_classes = ()
    serializer_class = ItemCategoryWithSubcategoriesSerializer
    queryset = ItemCategory.objects.all()

    def get_serializer_context(self):
        serializer = OptionalOrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _("Valid organization is required in query parameters")
            )

        context = super().get_serializer_context()
        context["organization"] = serializer.validated_data["organization"]

        return context


class ItemCategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = ItemCategorySerializer
    queryset = ItemCategory.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()

        purchase_type = self.request.query_params.get("purchase_type", None)

        if purchase_type:
            queryset = queryset.filter(purchase_type=purchase_type)

        return queryset


class ItemRentalCategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        try:
            return ItemCategory.objects.filter(
                Q(name__icontains="Rental")
                | Q(name__icontains="Аренда")
                | Q(name__icontains="Kiralama")
            )
        except ItemCategory.DoesNotExist:
            raise ObjectNotFoundException(_("ItemCategory not found"))


class ItemTicketCategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        try:
            return ItemCategory.objects.filter(
                Q(name__icontains="Subscription")
                | Q(name__icontains="Абонемент")
                | Q(name__icontains="Abonelik")
                | Q(name__icontains="Concert")
                | Q(name__icontains="Концерт")
                | Q(name__icontains="Konser")
                | Q(name__icontains="Event")
                | Q(name__icontains="Событие")
                | Q(name__icontains="Etkinlik")
                | Q(name__icontains="Presentation")
                | Q(name__icontains="Презентация")
                | Q(name__icontains="Sunum")
            )
        except ItemCategory.DoesNotExist:
            raise ObjectNotFoundException(_("ItemCategory not found"))


class ItemCategoryRetrieveView(RetrieveAPIView):
    permission_classes = ()
    serializer_class = ItemCategoryWithNonEmptySubcategoriesSerializer
    queryset = ItemCategory.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        qp_serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not qp_serializer.is_valid():
            raise NotAcceptableException(
                _("Valid country and city are required in query parameters")
            )

        context["city"] = qp_serializer.validated_data["city"]
        context["country"] = qp_serializer.validated_data["country"]

        return context


class NonEmptyCategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        qp_serializer = CountryCityQueryParamSerializer(data=self.request.GET)
        if not qp_serializer.is_valid():
            raise NotAcceptableException(
                _("Valid country and city are required in query parameters")
            )

        return ItemCategoryService.get_nonempty_general_categories(
            country=qp_serializer.validated_data["country"],
            city=qp_serializer.validated_data["city"],
        )


class NonEmptyPartnerCategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        main_organization = Organization.objects.get(id=self.kwargs["pk"])
        partners = (
            main_organization.requested_partnerships.filter(is_accepted=True)
            .values_list("accepted_by", flat=True)
            .distinct()
        )
        partner_organizations = Organization.objects.filter(
            Q(id__in=partners)
            | Q(id=self.kwargs["pk"])
            & Q(is_active=True, is_private=False, is_banned=False)
        )
        item_categories = ShopItem.objects.exclude(
            Q(organization__is_banned=True)
            | Q(organization__is_deleted=True)
            | Q(organization__is_private=True)
        )
        item_categories = (
            item_categories.filter(
                organization__in=partner_organizations, is_published=True
            )
            .values_list("subcategory_id", flat=True)
            .distinct()
        )
        return (
            ItemCategory.objects.filter(subcategories__in=item_categories)
            .distinct()
            .order_by("name")
        )


class NonEmptyPartnerSubcategoryListView(ListAPIView):
    permission_classes = ()
    pagination_class = None
    serializer_class = NonEmptyItemSubcategorySerializer

    def get_queryset(self):
        main_organization = Organization.objects.get(id=self.kwargs["pk"])
        partners = (
            main_organization.requested_partnerships.filter(is_accepted=True)
            .values_list("accepted_by", flat=True)
            .distinct()
        )
        partner_organizations = Organization.objects.filter(
            Q(id__in=partners) | Q(id=self.kwargs["pk"])
        )
        category_id = self.request.query_params.get("category")
        shop_items = (
            ShopItem.objects.filter(organization__in=partner_organizations)
            .values_list("id", flat=True)
            .distinct()
        )
        return (
            ItemSubcategory.objects.filter(category_id=category_id, id__in=shop_items)
            .distinct()
            .order_by("name")
        )


class SubcategoryRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItemSubcategory)
    serializer_class = ItemSubcategorySerializer
    queryset = ItemSubcategory.objects.all()


class ItemSubcategoryCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemSubcategoryCreateSerializer
    queryset = ItemSubcategory.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = ItemSubcategoryCreateSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        name_ru = GPTTranslator().translate(serializer.validated_data["name"], "ru")
        name_en = GPTTranslator().translate(serializer.validated_data["name"], "en")
        name_tr = GPTTranslator().translate(serializer.validated_data["name"], "tr")
        name_de = GPTTranslator().translate(serializer.validated_data["name"], "de")
        name_zh = GPTTranslator().translate(serializer.validated_data["name"], "zh-CN")
        subcategory = ItemSubcategory.objects.create(
            organization=serializer.validated_data["organization"],
            name=serializer.validated_data["name"],
            category=serializer.validated_data["category"],
            name_ru=name_ru,
            name_en=name_en,
            name_tr=name_tr,
            name_de=name_de,
            name_zh=name_zh,
        )
        subcategory.save()
        return Response(
            self.serializer_class(subcategory).data, status=status.HTTP_201_CREATED
        )


class OrganizationSubcategoryListView(ListAPIView):
    serializer_class = ItemSubcategoryBriefSerializer
    pagination_class = None

    def get_queryset(self):
        return ItemSubcategoryService.get_orgs_nonempty_subcategories(
            organization_id=self.kwargs["pk"]
        )
