from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.serializers.coupon_serializers import (
    CalculateCouponValidateSerializer,
    CouponDetailSerializer,
    CouponListForUserSerializer,
)
from organizations.services.coupon_services import CouponServiceClass


class AvailableCouponsListAPIView(GenericAPIView):
    serializer_class = CouponDetailSerializer
    service_class = CouponServiceClass
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        org_id = kwargs.get("pk")
        transaction_id = self.request.query_params.get("transaction_id")
        coupons = self.service_class.get_available(org_id, transaction_id)
        serializer = self.serializer_class(coupons, many=True)

        return Response(data=serializer.data, status=200)


class CalculateSumOfCouponsAPIView(GenericAPIView):
    serializer_class = CalculateCouponValidateSerializer
    permission_classes = [IsAuthenticated]
    service_class = CouponServiceClass

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid()
        result = self.service_class.calculate(serializer.validated_data)

        return Response(data=result, status=200)


class CouponsListForUsersAPIView(GenericAPIView):
    serializer_class = CouponListForUserSerializer
    permission_classes = [IsAuthenticated]
    service_class = CouponServiceClass

    def get(self, request, *args, **kwargs):
        org_id = kwargs.get("pk")
        user = request.user
        queryset = self.service_class.get_list(org_id, user)

        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=200)
