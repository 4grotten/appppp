from django.db.models import ProtectedError
from django.http import HttpResponse
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException
from organizations.models import Role, Membership
from organizations.permissions import IsAnyOrganizationOwnerOrAdmin
from organizations.serializers.membership_serializers import (
    MembershipSerializer, MembershipListSerializer, MembershipCreateSerializer, MembershipUpdateSerializer,
    RoleBriefSerializer, RoleSerializer, RoleCreateSerializer, TransferOwnershipSerializer,
)
from organizations.serializers.organization_serializers import OrganizationQueryParamSerializer
from organizations.services.membership_services import MembershipService, RoleService
from organizations.services.organization_services import OrganizationService
from users.models import User
from users.serializers import EmployeeSerializer


class MembershipListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MembershipListSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('user__id', 'user__phone_number', 'user__first_name', 'user__last_name',)

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        organization = serializer.validated_data['organization']
        if not OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user):
            raise NotAcceptableException('No rights to edit organization')
        return MembershipService.get_organization_employees(organization=organization)

    def create(self, request, *args, **kwargs):
        serializer = MembershipCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        MembershipService.add_employee(organization=serializer.validated_data['organization'],
                                       employee=serializer.validated_data['user'],
                                       role=serializer.validated_data['role'],
                                       added_by=request.user)

        return Response(data={'message': 'Successfully created'}, status=status.HTTP_201_CREATED)


class MembershipRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MembershipSerializer
    queryset = Membership.objects.all()

    def get_object(self):
        membership = MembershipService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_edit_organization(organization=membership.organization,
                                                              user=self.request.user):
            raise NotAcceptableException('No rights to edit organization')
        return membership

    def delete(self, request, *args, **kwargs):
        membership = MembershipService.get(id=self.kwargs['pk'])
        MembershipService.dismiss_employee(membership)
        return HttpResponse(status=204)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MembershipUpdateSerializer(instance, data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        membership = MembershipService.update_role(membership=instance, new_role=serializer.validated_data['role'])
        return Response(MembershipSerializer(membership).data)


class RolesListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RoleBriefSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('title',)

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


class RoleRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
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


class TransferOwnershipView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransferOwnershipSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        OrganizationService.change_organization_owner(organization=serializer.validated_data['organization'],
                                                      new_owner=serializer.validated_data['new_owner'],
                                                      current_owner=request.user)

        return Response(data={'message': 'Successfully transferred ownership'}, status=status.HTTP_200_OK)


class BriefUserInfoView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAnyOrganizationOwnerOrAdmin)
    serializer_class = EmployeeSerializer
    queryset = User.objects.filter(is_active=True)
