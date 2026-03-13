from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OrganizationLinkRequestSerializer
from .services import ApofizOrganizationLinkService


class OrganizationLinkAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = OrganizationLinkRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return self._build_response(
            organization_id=serializer.validated_data["organization_id"],
            include_applications=serializer.validated_data["include_applications"],
        )

    def post(self, request):
        serializer = OrganizationLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._build_response(
            organization_id=serializer.validated_data["organization_id"],
            include_applications=serializer.validated_data["include_applications"],
        )

    @staticmethod
    def _build_response(organization_id: int, include_applications: bool = False):
        links = ApofizOrganizationLinkService.build_links(organization_id)
        is_ok, organization_payload, organization_status = (
            ApofizOrganizationLinkService.fetch_organization(organization_id)
        )

        organization_title = None
        if isinstance(organization_payload, dict):
            organization_title = organization_payload.get("title")

        organization_page_url = ApofizOrganizationLinkService.build_organization_page_url(
            organization_id=organization_id,
            organization_name=organization_title,
        )

        if organization_status == 404:
            return Response(
                {
                    "organization_id": organization_id,
                    "exists": False,
                    "organization_url": links["organization_url"],
                    "applications_url": links["applications_url"],
                    "organization_page_url": organization_page_url,
                    "error": "Organization not found in partner API",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not is_ok:
            # Return 503 Service Unavailable instead of 502 for better client UX
            # 502 = our service is down, 503 = upstream service is down
            return Response(
                {
                    "organization_id": organization_id,
                    "exists": False,
                    "organization_url": links["organization_url"],
                    "applications_url": links["applications_url"],
                    "organization_page_url": organization_page_url,
                    "error": "Apofiz API is temporarily unavailable",
                    "details": organization_payload,
                    "partner_status_code": organization_status,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        applications_payload = None
        applications_status = None
        if include_applications:
            _, applications_payload, applications_status = (
                ApofizOrganizationLinkService.fetch_applications(organization_id)
            )

        return Response(
            {
                "organization_id": organization_id,
                "exists": True,
                "organization_url": links["organization_url"],
                "applications_url": links["applications_url"],
                "organization_page_url": organization_page_url,
                "partner_organization": organization_payload,
                "partner_organization_status": organization_status,
                "partner_applications": applications_payload,
                "partner_applications_status": applications_status,
            }
        )
