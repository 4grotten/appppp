from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException
from common.permissions import ReadOnly
from organizations.serializers.hotlink_serializers import (
    HotlinkSerializer, HotlinkCreateSerializer, HotlinkUpdateSerializer
)
from organizations.serializers.query_param_serializers import OrganizationQueryParamSerializer
from organizations.services.hotlink_services import HotlinkService


class HotlinkListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated | ReadOnly]
    serializer_class = HotlinkSerializer

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Wrong organization parameter'))
        return HotlinkService.get_hotlinks(organization=serializer.validated_data['organization'])

    def post(self, request, *args, **kwargs):
        serializer = HotlinkCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        HotlinkService.create_hotlink(
            user=request.user,
            organization=serializer.validated_data['organization'],
            link=serializer.validated_data['link'],
            image=serializer.validated_data['image']
        )

        return Response(data={
            'message': 'Successfully created',
        }, status=status.HTTP_201_CREATED)


class HotlinkRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = HotlinkSerializer

    def get_object(self):
        return HotlinkService.get_editable_hotlink_for_user(hotlink_id=self.kwargs['pk'], user=self.request.user)

    def put(self, request, *args, **kwargs):
        serializer = HotlinkUpdateSerializer(data=request.data)
        instance = self.get_object()
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        hotlink = HotlinkService.update_hotlink(
            hotlink=instance,
            link=serializer.validated_data['link'],
            image=serializer.validated_data['image']
        )
        hotlink = HotlinkSerializer(hotlink, context={'request': request}).data
        return Response(hotlink)
