import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from organizations.models import Organization
from organizations.services.ai_access_service import check_gemini_access


logger = logging.getLogger(__name__)


@require_GET
def gemini_access_check_view(request):
    organization_id = request.GET.get("organization_id")
    if not organization_id:
        logger.warning("[GEMINI_ACCESS][INTERNAL] denied: missing organization_id")
        return JsonResponse({"detail": "organization_id is required"}, status=400)

    try:
        organization_id = int(organization_id)
    except (TypeError, ValueError):
        logger.warning(
            "[GEMINI_ACCESS][INTERNAL] denied: invalid organization_id=%s",
            organization_id,
        )
        return JsonResponse({"detail": "organization_id must be an integer"}, status=400)

    organization = Organization.objects.filter(pk=organization_id).only("id", "gemini_enabled").first()
    if not organization:
        logger.warning(
            "[GEMINI_ACCESS][INTERNAL] denied: org_id=%s not found",
            organization_id,
        )
        return JsonResponse(
            {"organization_id": organization_id, "allowed": False, "detail": "organization_not_found"},
            status=404,
        )

    allowed = check_gemini_access(organization)
    logger.info(
        "[GEMINI_ACCESS][INTERNAL] org_id=%s allowed=%s",
        organization.id,
        allowed,
    )
    return JsonResponse({"organization_id": organization.id, "allowed": allowed})
