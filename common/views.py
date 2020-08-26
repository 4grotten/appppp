import re
from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated

from organizations.services.organization_services import OrganizationService
from .models import File, Country
from .serializers import ImageSerializer, CountrySerializer


class ImageCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    serializer_class = ImageSerializer
    queryset = File.objects.all()


class CountriesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CountrySerializer
    queryset = Country.objects.all()
    pagination_class = None


def index(request):
    return render(request, 'dist/index.html', {})


def organization_detail_view(request, pk):
    organization = OrganizationService.get(pk=pk)
    description = organization.description
    # description = description.replace(r'\n', ' ').replace(r'\r', '')
    description1 = re.sub("\n|\r", " ", description)

    context = {
        'organization': organization,
        'description': description1
    }
    return render(request, 'dist/index.html', context)
