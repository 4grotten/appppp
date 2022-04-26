from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.pagination import GeneralPagination
from organizations.services.organization_services import OrganizationService
from shop.models import Comment
from shop.serializers.comment_serializers import CommentSerializer, CommentLikeSerializer, CommentCreateSerializer
from shop.serializers.item_serializers import SubscriptionItemSerializer
from shop.services.comment_services import CommentService
from shop.services.item_services import ShopItemService
from shop.services.like_bookmark_services import LikeService


class CommentItemListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = CommentSerializer

    def get_queryset(self):
        item = ShopItemService.get(id=self.kwargs['pk'])
        return Comment.objects.filter(item=item).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        item = ShopItemService.get(id=self.kwargs['pk'])
        response = super().list(request, args, kwargs)
        response.data['my_role'] = CommentService.get_my_role(user=self.request.user, item=item)
        response.data['wallpapers'] = CommentService.get_wallpapers()
        return response

    def create(self, request, *args, **kwargs):
        serializer = CommentCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        item = ShopItemService.get(id=self.kwargs['pk'])
        comment = CommentService.create_comment(**serializer.validated_data, item=item)
        data = self.serializer_class(comment, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class CommentDestroyUpdateRetrievtView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def delete(self, request, *args, **kwargs):
        try:
            comment = Comment.objects.get(id=self.kwargs['pk'])
        except Comment.DoesNotExist:
            raise ObjectNotFoundException(_('Comment not found'))

        organization = OrganizationService.get(id=comment.item.organization.id)
        if OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user) or \
                self.request.user == comment.user:
            CommentService.delete_comment(comment=comment)
            return Response(data={
                'message': _('Successfully deleted comment'),
            }, status=status.HTTP_204_NO_CONTENT)
        raise NotAcceptableException(_('No rights to delete comment'))


class CommentedItemsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = SubscriptionItemSerializer

    def get_queryset(self):
        qs = CommentService.get_commented_items(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)


class CommentLike(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = SubscriptionItemSerializer

    def create(self, request, *args, **kwargs):
        serializer = CommentLikeSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        LikeService.like_unlike_comment(user=request.user, comment=serializer.validated_data['comment'],
                                        is_liked=serializer.validated_data['is_liked'])

        return Response(data={'message': _('Successfully updated like status')})
