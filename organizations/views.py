from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Organization, OrganizationType
from .serializers import (
    OrganizationListSerializer, OrganizationCreateSerializer,
    OrganizationTypeSerializer, OrganizationSerializer
)


class OrganizationsListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(Q(owner=user) | Q(memberships__user=user))

    def create(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.save()

        data = OrganizationSerializer(organization, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationTypeSerializer
    queryset = OrganizationType.objects.all()
