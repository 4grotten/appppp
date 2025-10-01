from rest_framework import serializers


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
