from rest_framework import generics
from rest_framework.response import Response
from organizations.services.invoice_service import OrganizationInvoiceService
from organizations.serializers.invoice_serializers import (
    InvoiceCreateSerializer,
    InvoiceModelSerializer,
    InvoiceInformationListSerializer,
    InvoiceInformationSerializer,
    InvoiceListSerializer,
    ReceiptListSerializer,
)
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
        return Response(
            data={"message": "successfully created invoice", "invoice_number": data},
            status=200,
        )


class OrganizationGetInvoiceAPIView(generics.GenericAPIView):
    serializer_class = InvoiceModelSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        invoice_number = kwargs.get("invoice_number", None)
        if not invoice_number:
            raise ValueError()

        data = self.service_class.get_invoice_by_invoice_number(invoice_number)

        serializer = self.serializer_class(instance=data)
        return Response(serializer.data, status=200)


class OrganizationGetInvoiceInformationListAPIView(generics.GenericAPIView):
    serializer_class = InvoiceInformationListSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        org_id = kwargs.get("pk")
        info_type = self.request.query_params.get("type")
        if not info_type:
            raise ValueError("type parameter is required!")
        qs = self.service_class.get_invoice_informations_list(
            org_id, self.request.user, info_type
        )
        serializer = self.serializer_class(instance=qs, many=True)
        return Response(data=serializer.data, status=200)


class OrganizationGetInvoiceInformationAPIView(generics.GenericAPIView):
    serializer_class = InvoiceInformationSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        information_id = kwargs.get("pk")
        qs = self.service_class.get_invoice_information(
            self.request.user, information_id
        )

        serializer = self.serializer_class(instance=qs)

        return Response(data=serializer.data, status=200)


class OrganizationInvoiceListAPIView(generics.GenericAPIView):
    serializer_class = InvoiceListSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        org_id = kwargs.get("pk")

        qs = self.service_class.get_invoice_list(request.user, org_id)
        serializer = self.serializer_class(instance=qs, many=True)

        return Response(data=serializer.data, status=200)


class OrganizationReceiptListAPIView(generics.GenericAPIView):
    serializer_class = ReceiptListSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        org_id = kwargs.get("pk")

        qs = self.service_class.get_receipt_list(request.user, org_id)

        serializer = self.serializer_class(instance=qs, many=True)

        return Response(serializer.data, status=200)
