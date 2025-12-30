from django.shortcuts import render

from organizations.services.organization_services import OrganizationService


def org_detail(request, pk):
    organization = OrganizationService.get(pk=pk)

    # Prepare description for OG tag (truncate if too long)
    description = ""
    if organization and organization.description:
        description = organization.description[:200]
        if len(organization.description) > 200:
            description += "..."

    # Get image URL
    image_url = "https://apofiz.com/static/assets/logo192.png"
    if organization and organization.image and organization.image.file:
        image_url = f"https://apofiz.com{organization.image.file.url}"

    context = {
        'organization': organization,
        'description': description,
        'image_url': image_url,
        'og_url': f"https://apofiz.com/organizations/{pk}",
    }

    return render(request, 'organization_detail.html', context)
