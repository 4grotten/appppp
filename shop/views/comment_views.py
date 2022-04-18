from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.pagination import GeneralPagination
from shop.models import Comment
from shop.serializers.comment_serializers import CommentSerializer
from shop.services.item_services import ShopItemService


class CommentItemListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = CommentSerializer

    def get_queryset(self):
        item = ShopItemService.get(id=self.kwargs['pk'])
        return Comment.objects.filter(item=item)
