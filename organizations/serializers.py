from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import FileSerializer
from .models import (
    Organization, OrganizationType, PhoneNumber,
    SocialNetworkContact, OrganizationCategory, DiscountCard, Subscription
)
from .services import OrganizationService, DiscountCardService, SubscriptionService


class DiscountCardSerializer(serializers.ModelSerializer):
    image = FileSerializer(read_only=True)
    organization_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DiscountCard
        fields = ('id', 'type', 'percent', 'limit', 'currency', 'image', 'organization_id',)

    def validate(self, attrs):
        if attrs['type'] == DiscountCard.CUMULATIVE:
            errors = {}
            if attrs.get('limit', None) is None:
                errors['limit'] = ['This field is required']
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class UserFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request')
        organization_id = request.data['organization']
        queryset = Organization.objects.filter(id=organization_id)

        if not queryset or not OrganizationService.user_can_edit_organization(
                organization_id=organization_id, user=request.user):
            raise NotAcceptableException('No rights to edit organization')

        return queryset


class DiscountBulkCreateSerializer(serializers.Serializer):
    cards = DiscountCardSerializer(many=True)
    organization = UserFilteredPrimaryKeyRelatedField(write_only=True)


class DiscountGroupSerializer(serializers.Serializer):
    cumulative = DiscountCardSerializer(many=True)
    fixed = DiscountCardSerializer(many=True)


class DiscountCardUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField(required=True, allow_null=True)

    class Meta:
        model = DiscountCard
        fields = ('image_id',)


class OrgPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ('id', 'phone_number')


class OrgPhoneNumberEditSerializer(serializers.Serializer):
    phone_numbers = serializers.ListSerializer(child=serializers.CharField())


class OrgSocialNetworkContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialNetworkContact
        fields = ('id', 'url')


class OrgSocialNetworkEditSerializer(serializers.Serializer):
    networks = serializers.ListSerializer(child=serializers.CharField())


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ('id', 'title',)


class OrganizationSerializer(serializers.ModelSerializer):
    image = FileSerializer(many=False)
    role = serializers.SerializerMethodField()
    types = serializers.StringRelatedField(many=True)

    def get_role(self, organization: Organization):
        user = self.context['request'].user
        return OrganizationService.get_user_role_in_organization(organization=organization, user=user)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'role', 'description', 'image_id',
                  'opens_at', 'closes_at', 'show_contacts', 'types', 'full_location', 'address')


class OrganizationWithImageSerializer(serializers.ModelSerializer):
    image = FileSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image')


class OrganizationDetailedSerializer(serializers.ModelSerializer):
    image = FileSerializer()
    permissions = serializers.SerializerMethodField()
    types = OrganizationTypeSerializer(many=True)
    phone_numbers = OrgPhoneNumberSerializer(many=True)
    social_contacts = OrgSocialNetworkContactSerializer(many=True)
    subscribers = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    saved_amount = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    active_card = serializers.SerializerMethodField()
    partners = serializers.SerializerMethodField()

    def get_permissions(self, organization: Organization):
        return OrganizationService.get_user_permissions_dict(organization=organization,
                                                             user=self.context['request'].user)

    def get_subscribers(self, organization: Organization):
        return SubscriptionService.get_number_of_subscriptions(organization=organization)

    def get_discounts(self, organization: Organization):
        discounts = DiscountCardService.get_grouped_discounts(organization_id=organization.id)
        return DiscountGroupSerializer(discounts).data

    def get_is_subscribed(self, organizaiton: Organization):
        return SubscriptionService.is_subscribed(organization=organizaiton, user=self.context['request'].user)

    def get_saved_amount(self, organizaiton: Organization):
        # ToDo Implement
        return 0

    def get_active_card(self, organizaiton: Organization):
        # ToDo Implement
        card = DiscountCard.objects.filter(organization=organizaiton, type=DiscountCard.CUMULATIVE).first()
        if card:
            return {
                'cumulative': card.id,
                'sum': 93000,
                'next': 100000
            }
        return {
            'cumulative': None,
            'sum': 0,
            'next': 0
        }

    def get_partners(self, organizaiton: Organization):
        count, partners = OrganizationService.get_partners_dict(organization=organizaiton)
        return {
            'count': count,
            'list': OrganizationWithImageSerializer(partners, many=True).data
        }

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'image', 'subscribers', 'description', 'currency',
            'show_contacts', 'opens_at', 'closes_at', 'address', 'full_location',
            'types', 'phone_numbers', 'social_contacts', 'discounts',
            'saved_amount', 'is_subscribed', 'permissions', 'active_card', 'partners',
        )


class OrganizationListSerializer(serializers.ModelSerializer):
    image = FileSerializer(many=False)
    role = serializers.SerializerMethodField()

    def get_role(self, organization: Organization):
        user = self.context['request'].user
        return OrganizationService.get_user_role_in_organization(organization=organization, user=user)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'role')


class OrganizationCreateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField()
    numbers = serializers.ListSerializer(child=serializers.CharField())
    accounts = serializers.ListSerializer(child=serializers.CharField())
    longitude = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)
    cards = DiscountCardSerializer(many=True)

    class Meta:
        model = Organization
        fields = (
            'title', 'description', 'image_id', 'currency',
            'opens_at', 'closes_at', 'address', 'longitude', 'latitude',
            'types', 'numbers', 'accounts', 'cards'
        )

    def validate(self, attrs):
        attrs['owner'] = self.context['request'].user
        return attrs


class OrganizationCategorySerializer(serializers.ModelSerializer):
    types = OrganizationTypeSerializer(many=True)

    class Meta:
        model = OrganizationCategory
        fields = ('id', 'name', 'types')


class LocationSerializer(serializers.Serializer):
    address = serializers.CharField()
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('organization',)
