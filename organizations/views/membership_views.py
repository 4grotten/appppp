from django.db.models import ProtectedError
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.models import Role
from organizations.serializers.membership_serializers import (
    MembershipSerializer, RoleBriefSerializer, RoleSerializer, RoleCreateSerializer
)
from organizations.serializers.organization_serializers import OrganizationQueryParamSerializer
from organizations.services.membership_services import MembershipService, RoleService
from organizations.services.organization_services import OrganizationService


class MembershipAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MembershipSerializer

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user):
            raise NotAcceptableException('No rights to edit organization')
        return MembershipService.get_organization_employees(organization=organization)


class RolesListCreateAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RoleBriefSerializer

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user):
            raise NotAcceptableException('No rights to edit organization')
        return RoleService.filter(organization=organization)

    def create(self, request, *args, **kwargs):
        self.serializer_class = RoleCreateSerializer
        return super().create(request, *args, **kwargs)


class RoleRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RoleSerializer
    queryset = Role.objects.all()

    def get_object(self):
        role = RoleService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=role.organization, user=self.request.user):
            raise NotAcceptableException('No rights to edit organization')
        return role

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise NotAcceptableException('There are existing employees with this role')
