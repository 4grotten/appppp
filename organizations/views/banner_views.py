from rest_framework import status
from rest_framework.generics import GenericAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import Banner
from organizations.serializers.banner_serializers import (
    BannerSerializer, OrganizationIDSerializer, BannerCreateSerializer
)
from organizations.services.banner_services import BannerService


class BannerView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = OrganizationIDSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        banners = BannerService.get_banners(organization=serializer.validated_data['organization'])
        banners = BannerSerializer(banners, many=True, context={'request': request}).data

        return Response(banners)

    def post(self, request, *args, **kwargs):
        serializer = BannerCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        BannerService.create_banner(
            user=request.user,
            host=serializer.validated_data['host_organization'],
            linked_to=serializer.validated_data['linked_organization'],
            image=serializer.validated_data['image']
        )

        return Response(data={
            'message': 'Successfully created',
        }, status=status.HTTP_201_CREATED)


class BannerDeleteView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Banner.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        BannerService.delete_banner(user=request.user, banner=instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
