from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from organizations.models import Organization
from organizations.services.ai_access_service import check_gemini_access

from organizations.serializers.invoice_serializers import (
    ActiveTariffSerializer,
    InvoiceCreateSerializer,
    InvoiceInformationListSerializer,
    InvoiceInformationSerializer,
    InvoiceListSerializer,
    InvoiceModelSerializer,
    ReceiptListSerializer,
)
from organizations.services.invoice_service import OrganizationInvoiceService


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


class OrganizationActiveTariffAPIView(generics.GenericAPIView):
    serializer_class = ActiveTariffSerializer
    service_class = OrganizationInvoiceService
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")

        qs = self.service_class.get_active_tariff(pk)

        if qs is None:
            organization = Organization.objects.filter(pk=pk).only(
                "id",
                "gemini_enabled",
                "ai_trial_enabled",
                "ai_trial_started_at",
                "ai_trial_ends_at",
                "ai_trial_web_chat_enabled",
                "ai_trial_telegram_enabled",
                "ai_trial_whatsapp_enabled",
            ).first()

            if organization and check_gemini_access(organization):
                return Response(
                    {
                        "tariff": {
                            "tariff_type": "gemini_access",
                            "original_price": 0,
                            "duration_months": 0,
                            "total_price": 0,
                            "discount": 0,
                        },
                        "is_active": True,
                        "active_until": timezone.now(),
                    },
                    status=200,
                )

        serializer = self.serializer_class(instance=qs)

        return Response(serializer.data, status=200)


class CreateOrganizationInfoAPIView(generics.GenericAPIView):
    serializer_class = InvoiceCreateSerializer
    service_class = OrganizationInvoiceService

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid()
        data = serializer.data.get("data")
        organization_id = serializer.data.get("organization")
        self.service_class.get_or_create_info(data, organization_id)

        return Response(
            data={"message": "successfully created/updated organization invoice data"},
            status=200,
        )


class AIPaymentSystemsListAPIView(generics.GenericAPIView):
    """
    Возвращает список платёжных систем, доступных для оплаты AI ассистента.
    Фильтрует по флагу is_available_for_ai=True в админке.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from organizations.services.regional_payment_service import (
            RegionalPaymentSystemService,
        )

        payment_systems = RegionalPaymentSystemService.get_available_for_ai()

        return Response(data=payment_systems, status=200)
