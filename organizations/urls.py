from django.urls import path

from .views import OrganizationsListCreateView, OrganizationTypesListView

urlpatterns = [
    path('organizations/', OrganizationsListCreateView.as_view(), name='user-organizations'),
    path('organization_types/', OrganizationTypesListView.as_view(), name='organization-types')
]
