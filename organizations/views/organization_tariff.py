from rest_framework import generics
from rest_framework.response import Response
from organizations.services.invoice_service import OrganizationInvoiceService
from organizations.serializers.invoice_serializers import InvoiceCreateSerializer
from rest_framework.permissions import IsAuthenticated


class OrganizationTariffInvoiceAPIView(generics.GenericAPIView):
    serializer_class = InvoiceCreateSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.service_class.create_invoice(
            **serializer.validated_data, user=request.user
        )
        return Response(data={"message": "succsefull"})
