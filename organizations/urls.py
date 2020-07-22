from django.urls import path

from .views.subscription_views import SubscriptionsView
from .views.card_views import OrganizationDiscountsAPIView, OrganizationDiscountsDeleteUpdateView, BackgroundListView
from .views.organization_views import (
    OrganizationsListCreateView, OrganizationTypesListView, OrganizationRetrieveView,
    OrgPhonesListAPIView, OrgNetworksListAPIView, SetOrganizationLocationAPIView
)
from .views.discount_views import DiscountsBulkUpdateView, DiscountsBulkDeleteView
from .views.partnerships_views import PartnershipView, OrganizationPartnersView

urlpatterns = [
    path('organization_types/', OrganizationTypesListView.as_view(), name='organization_types'),

    path('organizations/', OrganizationsListCreateView.as_view(), name='user_organizations'),
    path('organizations/<int:pk>/', OrganizationRetrieveView.as_view(), name='organization_details'),
    path('organizations/<int:pk>/phone_numbers/', OrgPhonesListAPIView.as_view(), name='organization_phones'),
    path('organizations/<int:pk>/social_networks/', OrgNetworksListAPIView.as_view(), name='organization_networks'),
    path('organizations/<int:pk>/location/', SetOrganizationLocationAPIView.as_view(), name='set_location'),
    path('organizations/<int:pk>/partners/', OrganizationPartnersView.as_view(), name='organization_partners'),

    path('discounts/', OrganizationDiscountsAPIView.as_view(), name='discounts'),
    path('discounts/<int:pk>/', OrganizationDiscountsDeleteUpdateView.as_view(), name='discounts_delete'),
    path('discounts/doBulkUpdate/', DiscountsBulkUpdateView.as_view(), name='discounts_bulk_update'),
    path('discounts/doBulkDelete/', DiscountsBulkDeleteView.as_view(), name='discounts_bulk_delete'),

    path('discount_backgrounds/', BackgroundListView.as_view(), name='backgrounds'),

    path('subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),

    path('partnerships/', PartnershipView.as_view(), name='partnerships'),
]
