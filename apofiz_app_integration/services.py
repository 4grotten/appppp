from urllib.parse import urlencode
from typing import Any, Optional, Tuple

from django.conf import settings
import requests
import re


class ApofizOrganizationLinkService:
    @classmethod
    def get_base_api_url(cls) -> str:
        return getattr(settings, "APOFIZ_INTEGRATION_BASE_API_URL", "https://apofiz.com/api/v1").rstrip("/")

    @classmethod
    def get_request_timeout(cls) -> int:
        return getattr(settings, "APOFIZ_INTEGRATION_TIMEOUT", 10)

    @classmethod
    def get_org_page_base_url(cls) -> str:
        return getattr(
            settings,
            "APOFIZ_INTEGRATION_ORG_PAGE_BASE_URL",
            "http://134.122.53.6:3010/organizations",
        ).rstrip("/")

    @classmethod
    def get_headers(cls) -> dict:
        token = getattr(settings, "APOFIZ_INTEGRATION_TOKEN", "")
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def build_links(cls, organization_id: int) -> dict:
        base = cls.get_base_api_url()
        organizations_url = f"{base}/organizations/{organization_id}/"
        applications_url = f"{base}/shop/organization_items/?{urlencode({'organization': organization_id})}"

        return {
            "organization_id": organization_id,
            "organization_url": organizations_url,
            "applications_url": applications_url,
        }

    @classmethod
    def _sanitize_org_name(cls, organization_name: str) -> str:
        normalized = re.sub(r"\s+", "_", organization_name.strip())
        normalized = re.sub(r"[^\w-]", "", normalized)
        return normalized or "organization"

    @classmethod
    def build_organization_page_url(
        cls,
        organization_id: int,
        organization_name: Optional[str] = None,
    ) -> str:
        base = cls.get_org_page_base_url()
        if organization_name:
            safe_name = cls._sanitize_org_name(organization_name)
            return f"{base}/{organization_id}_{safe_name}"
        return f"{base}/{organization_id}"

    @classmethod
    def fetch_organization(cls, organization_id: int) -> Tuple[bool, Any, Optional[int]]:
        links = cls.build_links(organization_id)
        try:
            response = requests.get(
                links["organization_url"],
                headers=cls.get_headers(),
                timeout=cls.get_request_timeout(),
            )
        except requests.RequestException as exc:
            return False, str(exc), None

        if response.status_code == 404:
            return False, None, 404

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        return response.ok, payload, response.status_code

    @classmethod
    def fetch_applications(cls, organization_id: int) -> Tuple[bool, Any, Optional[int]]:
        links = cls.build_links(organization_id)
        try:
            response = requests.get(
                links["applications_url"],
                headers=cls.get_headers(),
                timeout=cls.get_request_timeout(),
            )
        except requests.RequestException as exc:
            return False, str(exc), None

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        return response.ok, payload, response.status_code
