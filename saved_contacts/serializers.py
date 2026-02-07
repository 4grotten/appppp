import uuid

from rest_framework import serializers

from common.serializers import ImageSerializer
from .models import SavedContact


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer for validating payment method structure."""

    PAYMENT_TYPES = ['card', 'iban', 'crypto', 'paypal', 'applepay', 'googlepay', 'wallet', 'other']

    id = serializers.CharField(required=True)
    type = serializers.ChoiceField(choices=[(t, t) for t in PAYMENT_TYPES], required=True)
    label = serializers.CharField(required=True, max_length=255)
    value = serializers.CharField(required=True, max_length=500)
    network = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)


class ContactSocialLinkSerializer(serializers.Serializer):
    """Serializer for validating social link structure."""

    id = serializers.CharField(required=True)
    networkId = serializers.CharField(required=True, max_length=100)
    networkName = serializers.CharField(required=True, max_length=255)
    url = serializers.URLField(required=True, max_length=500)


class SavedContactSerializer(serializers.ModelSerializer):
    """Main serializer for SavedContact model."""

    avatar = ImageSerializer(read_only=True)
    avatar_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    payment_methods = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    social_links = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )

    class Meta:
        model = SavedContact
        fields = [
            'id',
            'full_name',
            'phone',
            'email',
            'company',
            'position',
            'avatar',
            'avatar_id',
            'avatar_url',
            'notes',
            'payment_methods',
            'social_links',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'avatar']

    def get_avatar_url(self, obj):
        """Return avatar URL."""
        return obj.avatar_url

    def validate_payment_methods(self, value):
        """Validate payment_methods structure."""
        if not isinstance(value, list):
            raise serializers.ValidationError("payment_methods must be a list")

        for item in value:
            serializer = PaymentMethodSerializer(data=item)
            if not serializer.is_valid():
                raise serializers.ValidationError(
                    f"Invalid payment method: {serializer.errors}"
                )
        return value

    def validate_social_links(self, value):
        """Validate social_links structure."""
        if not isinstance(value, list):
            raise serializers.ValidationError("social_links must be a list")

        for item in value:
            serializer = ContactSocialLinkSerializer(data=item)
            if not serializer.is_valid():
                raise serializers.ValidationError(
                    f"Invalid social link: {serializer.errors}"
                )
        return value


class SavedContactCreateSerializer(SavedContactSerializer):
    """Serializer for creating SavedContact."""

    def create(self, validated_data):
        """Create a new SavedContact."""
        avatar_id = validated_data.pop('avatar_id', None)
        if avatar_id:
            validated_data['avatar_id'] = avatar_id
        return super().create(validated_data)


class SavedContactUpdateSerializer(SavedContactSerializer):
    """Serializer for updating SavedContact."""

    full_name = serializers.CharField(required=False, max_length=255)

    def update(self, instance, validated_data):
        """Update SavedContact."""
        avatar_id = validated_data.pop('avatar_id', None)
        if avatar_id is not None:
            instance.avatar_id = avatar_id if avatar_id else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class SavedContactAvatarSerializer(serializers.Serializer):
    """Serializer for avatar upload."""

    file = serializers.ImageField(required=True)
