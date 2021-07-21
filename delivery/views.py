from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from delivery.delivery_services import DeliveryInfoService
from delivery.models import DeliveryInfo
from delivery.serializers import DeliveryAllItemsCountSerializer, DeliveryInfoListSerializer


class DeliveryItemsCountView(APIView):
    permission_classes = (IsAuthenticated,)

    # serializer_class = CartSerializer

    def get(self, request):
        count = DeliveryInfoService.get_all_items_count(user=self.request.user)
        data = DeliveryAllItemsCountSerializer({"count": count}).data
        return Response(data, status=status.HTTP_200_OK)


class DeliveryInfoListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeliveryInfoListSerializer

    def get_queryset(self):
        user = self.request.user
        return DeliveryInfoService.get_available_orders(user)

        # return DeliveryInfo.objects.all()
