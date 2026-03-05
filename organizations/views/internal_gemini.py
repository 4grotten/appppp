from django.http import JsonResponse
from django.views.decorators.http import require_GET

from organizations.models import Organization


@require_GET
def gemini_access_check_view(request):
    organization_id = request.GET.get("organization_id")
    if not organization_id:
        return JsonResponse({"detail": "organization_id is required"}, status=400)

    try:
        organization_id = int(organization_id)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "organization_id must be an integer"}, status=400)

    organization = Organization.objects.filter(pk=organization_id).only("id", "gemini_enabled").first()
    if not organization:
        return JsonResponse(
            {"organization_id": organization_id, "allowed": False, "detail": "organization_not_found"},
            status=404,
        )

    return JsonResponse({"organization_id": organization.id, "allowed": bool(organization.gemini_enabled)})
