from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from organizations.models import Service
from organizations.serializers.service_serializer import ServiceSerializer


class ServiceReadOnlySet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
