from django.shortcuts import render

from organizations.models import Organization


def org_detail(request, pk):
    try:
        organization = Organization.objects.select_related(
            'image', 'image__file'
        ).get(pk=pk)
    except Organization.DoesNotExist:
        organization = None

    context = {
        'organization': organization,
        'description': organization.description[:200] if organization and organization.description else ''
    }

    return render(request, 'organization_detail.html', context)
