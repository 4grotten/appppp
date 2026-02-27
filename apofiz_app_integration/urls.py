from django.urls import path

from .views import OrganizationLinkAPIView

urlpatterns = [
    path(
        "apofiz/app/integration/organizations/link/",
        OrganizationLinkAPIView.as_view(),
        name="apofiz-app-organization-link",
    ),
]
