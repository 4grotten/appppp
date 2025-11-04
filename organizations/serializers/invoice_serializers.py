from rest_framework import serializers
from organizations.models import Invoice, RegionalTariff
from organizations.utils import create_download_url


class InvoiceForOwnerSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    address = serializers.CharField()
    email = serializers.EmailField()


class InvoiceForCompanySerializer(InvoiceForOwnerSerializer):
    company_name = serializers.CharField()
    tax_id = serializers.CharField()


class InvoiceCreateSerializer(serializers.Serializer):
    OWNER = "owner"
    COMPANY = "company"
    type_choices = [(OWNER, "owner"), (COMPANY, "company")]
    invoice_type = serializers.ChoiceField(choices=type_choices)
    payment_method = serializers.CharField(max_length=255)
    tariff_id = serializers.IntegerField()
    organization = serializers.IntegerField()
    data = serializers.DictField()

    def validate(self, attrs):
        invoice_type = attrs.get("invoice_type")
        invoice_data = attrs.get("data", {})

        if invoice_type == self.OWNER:
            nested_serializer = InvoiceForOwnerSerializer(data=invoice_data)
        elif invoice_type == self.COMPANY:
            nested_serializer = InvoiceForCompanySerializer(data=invoice_data)
        else:
            raise serializers.ValidationError("Недопустимый тип счета")

        nested_serializer.is_valid(raise_exception=True)
        attrs["data"] = nested_serializer.validated_data
        return attrs


class InvoiceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"

    def to_representation(self, instance):
        url = create_download_url(instance.invoice_pdf)
        data = super().to_representation(instance)
        data["invoice_download"] = url

        return data


class InvoiceInformationListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()


class InvoiceInformationSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    email = serializers.EmailField()
    company_name = serializers.CharField()
    tax_id = serializers.CharField()


class InvoiceListSerializer(serializers.Serializer):
    code = serializers.CharField()
    invoice_number = serializers.CharField()
    invoice_pdf = serializers.URLField()
    invoice_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoice_tax = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()

    def to_representation(self, instance):
        url = create_download_url(instance.invoice_pdf)
        data = super().to_representation(instance)
        data["invoice_download"] = url

        return data


class ReceiptListSerializer(serializers.Serializer):
    code = serializers.CharField()
    invoice_number = serializers.CharField()
    receipt_pdf = serializers.URLField()
    invoice_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoice_tax = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()

    def to_representation(self, instance):
        url = create_download_url(instance.invoice_pdf)
        data = super().to_representation(instance)
        data["receipt_download"] = url

        return data


class RegionalTariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalTariff
        fields = ["tariff_type", "original_price", "duration_months"]


class ActiveTariffSerializer(serializers.Serializer):
    tariff = RegionalTariffSerializer()
    is_active = serializers.BooleanField()
    active_until = serializers.DateTimeField()
