from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView, GenericAPIView, CreateAPIView, ListAPIView, DestroyAPIView
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.exceptions import NotAcceptableException
from organizations.constants import HOTLINK_COLLECTION
from organizations.models import HotlinkCollectionLink
from organizations.serializers.hotlink_serializers import (
    HotlinkSerializer, HotlinkCreateSerializer, HotlinkUpdateSerializer, HotlinkSubcategoriesEditSerializer,
    HotlinkItemsEditSerializer, HotlinkCollectionLinkSerializer, HotlinkCollectionLinkUpdateSerializer,
    HotlinkWithCountsSerializer
)
from organizations.serializers.query_param_serializers import OrganizationQueryParamSerializer
from organizations.services.hotlink_services import HotlinkService, HotlinkCollectionLinkService
from shop.serializers.category_serializers import ItemSubcategoryForHotlinksSerializer
from shop.serializers.item_serializers import ItemInHotlinkCollectionSerializer


class HotlinkListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
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

        HotlinkService.create_hotlink(user=request.user, organization=serializer.validated_data['organization'],
                                      content=serializer.validated_data['content'],
                                      link_type=serializer.validated_data['link_type'],
                                      image=serializer.validated_data['image'])

        return Response(data={
            'message': _('Successfully created'),
        }, status=status.HTTP_201_CREATED)


class HotlinkRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = HotlinkWithCountsSerializer

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

        hotlink = HotlinkService.update_hotlink(hotlink=instance, image=serializer.validated_data['image'],
                                                content=serializer.validated_data['content'],
                                                link_type=serializer.validated_data['link_type'])
        return Response(self.get_serializer(hotlink).data)


class HotlinkItemsListUpdateView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = HotlinkWithCountsSerializer

    def get(self, request, *args, **kwargs):
        hotlink = HotlinkService.get(id=self.kwargs['pk'], link_type=HOTLINK_COLLECTION)
        queryset = HotlinkService.get_hotlink_collection_items(hotlink=hotlink, user=self.request.user)

        page = self.paginate_queryset(queryset)
        serializer = ItemInHotlinkCollectionSerializer(
            page, many=True, context={'request': request, 'hotlink': hotlink}
        )
        return self.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = HotlinkItemsEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        hotlink = HotlinkService.get(id=self.kwargs['pk'], link_type=HOTLINK_COLLECTION)
        HotlinkService.edit_hotlink_selected_items(
            hotlink=hotlink, added=serializer.validated_data['added'], removed=serializer.validated_data['removed'],
            user=request.user
        )
        serializer = self.get_serializer(hotlink)
        return Response(serializer.data)


class HotlinkSubcategoriesListUpdateView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = HotlinkWithCountsSerializer

    def get(self, request, *args, **kwargs):
        hotlink = HotlinkService.get(id=self.kwargs['pk'], link_type=HOTLINK_COLLECTION)
        queryset = HotlinkService.get_hotlink_collection_subcategories(hotlink=hotlink, user=self.request.user)
        serializer = ItemSubcategoryForHotlinksSerializer(
            queryset, many=True, context={'request': request, 'hotlink': hotlink}
        )
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = HotlinkSubcategoriesEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        hotlink = HotlinkService.get(id=self.kwargs['pk'], link_type=HOTLINK_COLLECTION)
        HotlinkService.edit_hotlink_selected_subcategories(
            hotlink=hotlink, added=serializer.validated_data['added'], removed=serializer.validated_data['removed'],
            user=request.user
        )
        serializer = self.get_serializer(hotlink)
        return Response(serializer.data)


class CollectionLinksCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = HotlinkCollectionLinkSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        HotlinkCollectionLinkService.create_collection_link(
            hotlink=serializer.validated_data['hotlink'], content=serializer.validated_data['content'],
            user=request.user
        )

        return Response(data={'message': _('Successfully created')}, status=status.HTTP_201_CREATED)


class CollectionLinksListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = HotlinkCollectionLinkSerializer
    pagination_class = None

    def get_queryset(self):
        hotlink = HotlinkService.get(id=self.kwargs['pk'])
        return HotlinkCollectionLinkService.get_collection_links(hotlink=hotlink, user=self.request.user)


class CollectionLinkUpdateDestroyView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = HotlinkCollectionLink.objects.all()

    def put(self, request, *args, **kwargs):
        instance = HotlinkCollectionLinkService.get(id=kwargs['pk'])
        serializer = HotlinkCollectionLinkUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        instance = HotlinkCollectionLinkService.update_collection_link(
            collection_link=instance, content=serializer.validated_data['content'], user=request.user
        )
        return Response(HotlinkCollectionLinkSerializer(instance).data)

    def delete(self, request, *args, **kwargs):
        instance = HotlinkCollectionLinkService.get(id=kwargs['pk'])
        HotlinkCollectionLinkService.delete_collection_link(collection_link=instance, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
