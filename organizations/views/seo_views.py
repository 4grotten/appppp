from django.shortcuts import render

from organizations.services.organization_services import OrganizationService


def org_detail(request, pk):
    organization = OrganizationService.get(pk=pk)

    context = {
        'organization': organization,
        'description': organization.description[:200] if organization.description else ''
    }

    return render(request, 'organization_detail.html', context)
