from django.db import IntegrityError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView, \
    GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, ObjectNotFoundException, BadRequestException, IntegrityException
from common.pagination import GeneralPagination
from organizations.serializers.assistant_serializers import ChatSettingsSerializer
from organizations.services.assistant_services import ChatService
from organizations.services.organization_services import OrganizationService
from shop.models import Comment, CommentComplaint, UserCommentTheme
from shop.serializers.comment_serializers import CommentSerializer, CommentLikeSerializer, CommentCreateSerializer, \
    CommentComplaintSerializer, CommentUpdateSerializer, ItemChangeCommentsDisabledSerializer, \
    UserCommentThemeSerializer
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
        comment_complaints_ids = CommentComplaint.objects.filter(user=self.request.user).values_list('comment_id', flat=True).distinct()
        return Comment.objects.filter(item=item).exclude(id__in=comment_complaints_ids).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        item = ShopItemService.get(id=self.kwargs['pk'])
        response = super().list(request, args, kwargs)
        response.data['my_role'] = CommentService.get_my_role(user=self.request.user, item=item)
        response.data['wallpapers'] = CommentService.get_user_theme_or_default(user=self.request.user)
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


class CommentChatListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = CommentSerializer

    def get_queryset(self):
        chat = ChatService.get(id=self.kwargs['pk'])
        comment_complaints_ids = CommentComplaint.objects.filter(user=self.request.user).values_list('comment_id', flat=True).distinct()
        return Comment.objects.filter(chat=chat).exclude(id__in=comment_complaints_ids).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        chat = ChatService.get(id=self.kwargs['pk'])
        response = super().list(request, args, kwargs)
        response.data['my_role'] = CommentService.get_my_role_for_chat(user=self.request.user, chat=chat)
        response.data['wallpapers'] = CommentService.get_user_theme_or_default(user=self.request.user)
        response.data['chat'] = ChatSettingsSerializer(chat).data
        return response

    def create(self, request, *args, **kwargs):
        serializer = CommentCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        chat = ChatService.get(id=self.kwargs['pk'])
        if chat.chat_by_org_user:
            comment = CommentService.create_chat_comment_without_assistant_response(**serializer.validated_data,
                                                                                    chat=chat)
        else:
            comment = CommentService.create_chat_comment_with_assistant_response(**serializer.validated_data,
                                                                                 chat=chat)
        data = self.serializer_class(comment, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class ItemChangeCommentsDisabledView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ItemChangeCommentsDisabledSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ShopItemService.update_comments_disabled_status(user=request.user, item=serializer.validated_data['item'],
                                                        is_disabled=serializer.validated_data['is_disabled'])

        return Response(data={'message': _('Successfully updated comments disabled status')})


class CommentDestroyUpdateRetrievtView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer = CommentUpdateSerializer(comment, data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = OrganizationService.get(id=comment.item.organization.id)
        if OrganizationService.user_can_edit_organization(organization=organization, user=self.request.user) or \
                self.request.user == comment.user:
            serializer.save()
            return Response(data={
                'message': _('Successfully updated comment'),
            }, status=status.HTTP_200_OK)
        raise NotAcceptableException(_('No rights to edit comment'))

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
            }, status=status.HTTP_200_OK)
        raise NotAcceptableException(_('No rights to delete comment'))


class CommentedItemsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = SubscriptionItemSerializer

    def get_queryset(self):
        type = self.request.GET.get('type', None)
        if type == 'income':
            qs = CommentService.get_income_commented_items(user=self.request.user)
            return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)
        elif type == 'outcome':
            qs = CommentService.get_outcome_commented_items(user=self.request.user)
            return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)
        else:
            raise BadRequestException('You need add valid parameters')


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


class CommentComplaintCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = CommentComplaint.objects.all()
    serializer_class = CommentComplaintSerializer

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except IntegrityError:
            raise IntegrityException(_('You have already complained about this comment'))


class UploadUserThemeImageView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UserCommentThemeSerializer(data=request.data)

        if serializer.is_valid():
            theme_type = serializer.validated_data['theme_type']
            theme_id = serializer.validated_data.get('theme_id')
            image_id = serializer.validated_data.get('image_id')

            response_data = CommentService.update_user_theme(user, theme_type, theme_id, image_id)

            if "error" in response_data:
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)