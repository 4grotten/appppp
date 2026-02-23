from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization
from shop.services.catalog_export_service import CatalogExportService


class DownloadOrganizationCatalogExcelView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        try:
            organization = Organization.objects.select_related("assistant").get(id=pk)
        except Organization.DoesNotExist:
            return Response(
                {"message": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if organization.owner_id != request.user.id:
            return Response(
                {"message": "Only organization owner can download catalog"},
                status=status.HTTP_403_FORBIDDEN,
            )

        excel_url = CatalogExportService.export_latest_catalog_to_excel(organization)
        if not excel_url:
            return Response(
                {"message": "Catalog JSON file not found or empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Catalog exported successfully",
                "organization_id": organization.id,
                "download_url": excel_url,
            },
            status=status.HTTP_200_OK,
        )
