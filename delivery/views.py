from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from delivery.delivery_services import DeliveryInfoService
from delivery.serializers import DeliveryAllItemsCountSerializer


class DeliveryItemsCountView(APIView):
    permission_classes = (IsAuthenticated,)

    # serializer_class = CartSerializer

    def get(self, request):
        count = DeliveryInfoService.get_all_items_count(user=self.request.user)
        data = DeliveryAllItemsCountSerializer({"count": count}).data
        return Response(data, status=status.HTTP_200_OK)

    # def get_queryset(self):
    #     pass
    #     # return Cart.objects.filter(
    #     #     user=self.request.user, is_open=True, organization__is_deleted=False
    #     # ).prefetch_related(Prefetch('items', queryset=CartItem.objects.order_by('-created_at')))
    #
    # def retrieve(self, request, *args, **kwargs):
    #     pass
    #     # self.serializer_class = EmployeeCartSerializer
    #     # return super().retrieve(request, *args, **kwargs)
