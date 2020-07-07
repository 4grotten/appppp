from django.urls import path

from .views import (
    OrganizationsListCreateView, OrganizationTypesListView, OrgPhonesListAPIView,
    OrgNetworksListAPIView, SetOrganizationLocationAPIView
)

urlpatterns = [
    path('organizations/', OrganizationsListCreateView.as_view(), name='user-organizations'),
    path('organization_types/', OrganizationTypesListView.as_view(), name='organization-types'),
    path('organizations/<int:pk>/phone_numbers/', OrgPhonesListAPIView.as_view(), name='organization_phones'),
    path('organizations/<int:pk>/social_networks/', OrgNetworksListAPIView.as_view(), name='organization_networks'),
    path('organizations/<int:pk>/location/', SetOrganizationLocationAPIView.as_view(), name='set_location'),
]
