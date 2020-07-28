from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.models import DiscountCard, Organization
from organizations.services.card_services import DiscountCardService
from organizations.services.organization_services import OrganizationService


class DiscountCardSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    organization_id = serializers.IntegerField(read_only=True)
    is_editable = serializers.SerializerMethodField()

    def get_is_editable(self, card: DiscountCard) -> bool:
        return DiscountCardService.is_card_editable(discount=card)

    class Meta:
        model = DiscountCard
        fields = ('id', 'type', 'percent', 'limit', 'currency', 'is_editable', 'image', 'organization_id',)

    def validate(self, attrs):
        if attrs['type'] == DiscountCard.CUMULATIVE:
            errors = {}
            if attrs.get('limit', None) is None:
                errors['limit'] = ['This field is required']
            if errors:
                raise serializers.ValidationError(errors)
        else:
            attrs['limit'] = None

        return attrs


class UserFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request')
        organization_id = request.data['organization']
        queryset = Organization.objects.filter(id=organization_id)
        organization = OrganizationService.get(id=organization_id)

        if not queryset or not OrganizationService.user_can_edit_organization(
                organization=organization, user=request.user):
            raise NotAcceptableException('No rights to edit organization')

        return queryset


class DiscountBulkCreateSerializer(serializers.Serializer):
    cards = DiscountCardSerializer(many=True)
    organization = UserFilteredPrimaryKeyRelatedField(write_only=True)


class DiscountGroupSerializer(serializers.Serializer):
    cumulative = DiscountCardSerializer(many=True)
    fixed = DiscountCardSerializer(many=True)


class DiscountCardUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = DiscountCard
        fields = ('image_id',)


class DiscountCardBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCard
        fields = ('id', 'percent',)
