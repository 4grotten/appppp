from django.shortcuts import render

from organizations.models import Organization


def org_detail(request, pk):
    try:
        organization = Organization.objects.get(pk=pk)

        description = ""
        if organization.description:
            description = organization.description[:200]

    except Organization.DoesNotExist:
        organization = None
        description = "Организация не найдена"

    context = {
        'organization': organization,
        'description': description
    }

    return render(request, 'organization_detail.html', context)
