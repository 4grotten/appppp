from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import FileSerializer
from .models import (
    Organization, OrganizationType, PhoneNumber,
    SocialNetworkContact, OrganizationCategory, DiscountCard
)
from .services import OrganizationService, DiscountCardService


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


class OrganizationDetailedSerializer(serializers.ModelSerializer):
    image = FileSerializer()
    can_edit = serializers.SerializerMethodField()
    types = serializers.StringRelatedField(many=True)
    phone_numbers = OrgPhoneNumberSerializer(many=True)
    social_contacts = OrgSocialNetworkContactSerializer(many=True)
    followers = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    user_savings = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    def get_can_edit(self, organization: Organization):
        return OrganizationService.user_can_edit_organization(
            organization_id=organization.id, user=self.context['request'].user)

    def get_followers(self, organization: Organization):
        # ToDo: create Follow model and calcualte it
        return 0

    def get_discounts(self, organization: Organization):
        discounts = DiscountCardService.get_grouped_discounts(organization_id=organization.id)
        return DiscountGroupSerializer(discounts).data

    def get_user_savings(self, organizaiton: Organization):
        # ToDo Implement
        return 0

    def get_is_following(self, organizaiton: Organization):
        # ToDo Implement
        return False

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'image', 'followers', 'user_savings', 'description',
            'full_location', 'address', 'show_contacts', 'phone_numbers', 'social_contacts',
            'is_following', 'can_edit', 'types', 'opens_at', 'closes_at', 'discounts',
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
    description = serializers.CharField(required=True, allow_blank=False)
    image_id = serializers.IntegerField()

    class Meta:
        model = Organization
        fields = ('title', 'description', 'image_id', 'opens_at', 'closes_at', 'show_contacts', 'types')

    def validate(self, attrs):
        attrs['owner'] = self.context['request'].user
        return attrs


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ('id', 'title',)


class OrganizationCategorySerializer(serializers.ModelSerializer):
    types = OrganizationTypeSerializer(many=True)

    class Meta:
        model = OrganizationCategory
        fields = ('id', 'name', 'types')


class LocationSerializer(serializers.Serializer):
    address = serializers.CharField()
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()


class DiscountCardSerializer(serializers.ModelSerializer):
    image = FileSerializer(read_only=True)
    organization_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DiscountCard
        fields = ('id', 'type', 'percent', 'limit', 'currency', 'image', 'organization_id',)

    def validate(self, attrs):
        if attrs['type'] == DiscountCard.CUMULATIVE:
            errors = {}

            if attrs.get('currency', None) is None:
                errors['currency'] = ['This field is required']
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
