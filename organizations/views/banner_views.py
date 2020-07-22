from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from organizations.serializers.banner_serializers import BannerSerializer, OrganizationIDSerializer
from organizations.services.banner_services import BannerService


class BannerView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        serializer = OrganizationIDSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        banners = BannerService.get_banners(organization=serializer.validated_data['organization'])
        banners = BannerSerializer(banners, many=True).data

        return Response(banners)
