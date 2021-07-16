from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated


class DeliveryItemsCountView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    # serializer_class = CartSerializer

    def get_queryset(self):
        pass
        # return Cart.objects.filter(
        #     user=self.request.user, is_open=True, organization__is_deleted=False
        # ).prefetch_related(Prefetch('items', queryset=CartItem.objects.order_by('-created_at')))

    def retrieve(self, request, *args, **kwargs):
        pass
        # self.serializer_class = EmployeeCartSerializer
        # return super().retrieve(request, *args, **kwargs)