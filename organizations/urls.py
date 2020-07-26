from django.urls import path, include

from .views.banner_views import BannerView, BannerDeleteView
from .views.card_views import OrganizationDiscountsAPIView, OrganizationDiscountsDeleteUpdateView, BackgroundListView
from .views.discount_views import DiscountsBulkUpdateView, DiscountsBulkDeleteView
from .views.organization_views import (
    OrganizationsListCreateView, OrganizationTypesListView, OrganizationRetrieveView,
    OrgMessageAPIView,
    OrgPhonesListAPIView, OrgNetworksListAPIView, SetOrganizationLocationAPIView, HomepageOrganizationsView,
    OrganizationsInCategoryView
)
from .views.partnerships_views import (
    PartnershipView, OrganizationPartnersView, HomepagePartnersView,
    HomepageBannersView, OrgPartnershipsView, PartnershipRetrieveUpdateView
)
from .views.subscription_views import SubscriptionsView

organization_urls = [
    path('organization_types/', OrganizationTypesListView.as_view(), name='organization_types'),

    path('organizations/', OrganizationsListCreateView.as_view(), name='user_organizations'),
    path('organizations/<int:pk>/', OrganizationRetrieveView.as_view(), name='organization_details'),
    path('organizations/<int:pk>/phone_numbers/', OrgPhonesListAPIView.as_view(), name='organization_phones'),
    path('organizations/<int:pk>/messages/', OrgMessageAPIView.as_view(), name='organization_messages'),
    path('organizations/<int:pk>/social_networks/', OrgNetworksListAPIView.as_view(), name='organization_networks'),
    path('organizations/<int:pk>/location/', SetOrganizationLocationAPIView.as_view(), name='set_location'),
    path('organizations/<int:pk>/partners/', OrganizationPartnersView.as_view(), name='organization_partners'),
]

discounts_urls = [
    path('discounts/', OrganizationDiscountsAPIView.as_view(), name='discounts'),
    path('discounts/<int:pk>/', OrganizationDiscountsDeleteUpdateView.as_view(), name='discounts_delete'),
    path('discounts/doBulkUpdate/', DiscountsBulkUpdateView.as_view(), name='discounts_bulk_update'),
    path('discounts/doBulkDelete/', DiscountsBulkDeleteView.as_view(), name='discounts_bulk_delete'),
    path('discount_backgrounds/', BackgroundListView.as_view(), name='discount_backgrounds'),
]

partnership_urls = [
    path('partnerships/', PartnershipView.as_view(), name='partnerships'),
    path('partnerships/<int:pk>/', PartnershipRetrieveUpdateView.as_view(), name='partnership_details'),
    path('organizations/<int:pk>/partnerships/', OrgPartnershipsView.as_view(), name='organization_partnerships'),
]

urlpatterns = [
    path('', include(organization_urls)),
    path('', include(discounts_urls)),
    path('', include(partnership_urls)),

    path('subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),

    path('banners/', BannerView.as_view(), name='banners'),
    path('banners/<int:pk>/', BannerDeleteView.as_view(), name='banner_delete'),
    path('homepage/partners/', HomepagePartnersView.as_view(), name='homepage_partners'),
    path('homepage/banner_info/', HomepageBannersView.as_view(), name='homepage_banners'),
    path('homepage/organizations/', HomepageOrganizationsView.as_view(), name='homepage_organizations'),

    path('categorized_organizations/', OrganizationsInCategoryView.as_view(), name='categorized_organizations'),
]
