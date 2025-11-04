from rest_framework import serializers
from organizations.models import Invoice, RegionalTariff
import boto3
from django.conf import settings


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
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        file_key = str(instance.invoice_pdf)
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "key": file_key,
                "ResponseContentDisposition": f'attachment; filename="{file_key.split("/")[-1]}"',
            },
            ExpiresIn=3600,
        )

        data = super().to_representation(instance)
        data["invoice_pdf"] = url

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


class ReceiptListSerializer(serializers.Serializer):
    code = serializers.CharField()
    invoice_number = serializers.CharField()
    receipt_pdf = serializers.URLField()
    invoice_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoice_tax = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()


class RegionalTariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalTariff
        fields = ["tariff_type", "original_price", "duration_months"]


class ActiveTariffSerializer(serializers.Serializer):
    tariff = RegionalTariffSerializer()
    is_active = serializers.BooleanField()
    active_until = serializers.DateTimeField()
