from django.urls import path

from .views import (
    OrganizationsListCreateView, OrganizationTypesListView, OrgPhonesListAPIView,
    OrgNetworksListAPIView, SetOrganizationLocationAPIView, OrganizationDiscountsAPIView,
    OrganizationDiscountsDeleteUpdateView, OrganizationRetrieveView, SubscriptionsView, BackgroundListView
)

urlpatterns = [
    path('organization_types/', OrganizationTypesListView.as_view(), name='organization-types'),

    path('organizations/', OrganizationsListCreateView.as_view(), name='user-organizations'),
    path('organizations/<int:pk>/', OrganizationRetrieveView.as_view(), name='organization-details'),
    path('organizations/<int:pk>/phone_numbers/', OrgPhonesListAPIView.as_view(), name='organization-phones'),
    path('organizations/<int:pk>/social_networks/', OrgNetworksListAPIView.as_view(), name='organization-networks'),
    path('organizations/<int:pk>/location/', SetOrganizationLocationAPIView.as_view(), name='set-location'),

    path('discounts/', OrganizationDiscountsAPIView.as_view(), name='discounts'),
    path('discounts/<int:pk>/', OrganizationDiscountsDeleteUpdateView.as_view(), name='discounts-delete'),

    path('discount_backgrounds/', BackgroundListView.as_view(), name='backgrounds'),

    path('subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),
]
