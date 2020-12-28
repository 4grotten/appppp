from django.db import IntegrityError
from rest_framework import status, permissions
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from common.exceptions import IntegrityException, NotAcceptableException
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, Complaint
from shop.permissions import CanEditItem, CanViewUnpublishedItem
from shop.serializers.item_serializers import (
    ItemCreateUpdateSerializer, ItemSerializer, ItemChangePublishedSerializer, ItemFeedSerializer
)
from shop.serializers.other_serializers import ComplaintSerializer
from shop.serializers.like_bookmark_serializers import LikeSerializer, BookmarkSerializer
from shop.services.cart_services import CartItemService
from shop.services.item_services import ShopItemService
from shop.services.like_bookmark_services import LikeService, BookmarkService


class ItemCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer


class ItemRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItem)
    serializer_class = ItemCreateUpdateSerializer
    queryset = ShopItem.objects.all()

    def put(self, request, *args, **kwargs):
        ShopItemService.delete_instagram_images(kwargs['pk'])
        return super().put(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            self.permission_classes = (AllowAny, CanViewUnpublishedItem,)
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        if not kwargs['pk'].isdigit():
            return Response(data={
                'details': 'Not found'
            }, status=status.HTTP_404_NOT_FOUND)

        self.serializer_class = ItemSerializer
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        CartItemService.delete_item_from_all_carts(item=ShopItem.objects.get(id=kwargs['pk']))
        return super().delete(self, request, *args, **kwargs)


class ItemChangePublishedStatusView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ItemChangePublishedSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ShopItemService.update_published_status(user=request.user, item=serializer.validated_data['item'],
                                                is_published=serializer.validated_data['is_published'])

        return Response(data={'message': 'Successfully updated published status'})


class LikeListCreateView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemFeedSerializer

    def get_queryset(self):
        qs = ShopItemService.get_liked_items(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def post(self, request):
        serializer = LikeSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        LikeService.like_unlike_item(user=request.user, item=serializer.validated_data['item'],
                                     is_liked=serializer.validated_data['is_liked'])

        return Response(data={'message': 'Successfully updated like status'})


class BookmarkListCreateView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemFeedSerializer

    def get_queryset(self):
        qs = ShopItemService.get_bookmarked_items(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def post(self, request):
        serializer = BookmarkSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        BookmarkService.add_remove_bookmarked_item(user=request.user, item=serializer.validated_data['item'],
                                                   is_bookmarked=serializer.validated_data['is_bookmarked'])

        return Response(data={'message': 'Successfully updated bookmark status'})


class ComplaintCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except IntegrityError:
            raise IntegrityException('You have already complained about this item')
