from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.coupon_serializers import CouponDetailSerializer
from organizations.services.coupon_services import CouponServiceClass


class AvailableCouponsListAPIView(GenericAPIView):
    serializer_class = CouponDetailSerializer
    service_class = CouponServiceClass
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        org_id = kwargs.get("pk")
        user = request.user
        coupons = self.service_class.get_available(org_id, user)
        serializer = self.serializer_class(coupons, many=True)

        return Response(data=serializer.data, status=200)
