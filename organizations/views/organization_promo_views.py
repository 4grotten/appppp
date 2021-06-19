from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.organization_promo_serializers import (
    OrganizationPromoSerializer, OrganizationPromoCreateSerializer, OrganizationPromoUpdateSerializer
)
from organizations.services.organization_promo_services import OrganizationPromoService


class OrganizationPromoCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationPromoCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = OrganizationPromoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        promo = OrganizationPromoService.create_organization_promo(
            user=request.user,
            organization=serializer.validated_data['organization'],
            total_cashback=serializer.validated_data['total_cashback'],
            cashback=serializer.validated_data['cashback'],
            image=serializer.validated_data['image']
        )
        data = OrganizationPromoSerializer(promo, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationPromoRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationPromoSerializer

    def get_object(self):
        return OrganizationPromoService.get_promo_for_user(
            organization_id=self.kwargs['org_id'], user=self.request.user
        )

    def put(self, request, *args, **kwargs):
        serializer = OrganizationPromoUpdateSerializer(data=request.data)
        instance = self.get_object()
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        promo = OrganizationPromoService.update_organization_promo(
            organization_promo=instance,
            total_cashback=serializer.validated_data['total_cashback'],
            cashback=serializer.validated_data['cashback'],
            image=serializer.validated_data['image'],
            changed_by=request.user
        )
        promo_data = OrganizationPromoSerializer(promo, context={'request': request}).data
        return Response(promo_data)
