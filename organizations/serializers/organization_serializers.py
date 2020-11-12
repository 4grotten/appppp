from rest_framework import serializers

from common.serializers import ImageSerializer, CountrySerializer, CitySerializer
from organizations.models import PhoneNumber, SocialNetworkContact, Organization, Message, Membership, User
from organizations.serializers.card_serializers import DiscountGroupSerializer, DiscountCardSerializer
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from users.serializers import UserShortInfoSerializer


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
    image = ImageSerializer(many=False)
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
    image = ImageSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image')


class OrganizationWithTypeImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types')


class ItemFeedOrganizationSerializer(OrganizationWithTypeImageSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'title', 'currency', 'image', 'types')


class OrganizationShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'title',)


class PartnerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    partners = serializers.SerializerMethodField()

    def get_partners(self, organization: Organization):
        count, partners = OrganizationService.get_partners_dict(organization=organization)
        return {
            'count': count,
            'list': OrganizationWithImageSerializer(partners, many=True).data
        }

    class Meta:
        model = Organization
        fields = ('id', 'title', 'address', 'image', 'types', 'partners')


class PartnerWithLatestTransactionSerializer(PartnerSerializer):
    latest_transaction_time = serializers.SerializerMethodField()

    def get_latest_transaction_time(self, organization: Organization):
        # Annotated field
        return organization.latest_transaction_time

    class Meta:
        model = Organization
        fields = ('id', 'title', 'address', 'latest_transaction_time', 'image', 'types', 'partners')


class HomepagePartnerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    partners = serializers.SerializerMethodField()

    def get_partners(self, organization: Organization):
        partners = OrganizationService.get_organization_partners(organization=organization)
        return OrganizationWithImageSerializer(partners, many=True).data

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types', 'partners')


class OrganizationDetailedSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    permissions = serializers.SerializerMethodField()
    types = OrganizationTypeSerializer(many=True)
    phone_numbers = OrgPhoneNumberSerializer(many=True)
    social_contacts = OrgSocialNetworkContactSerializer(many=True)
    subscribers = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    client_status = serializers.SerializerMethodField()
    partners = serializers.SerializerMethodField()
    country = CountrySerializer()
    city = CitySerializer()
    currency_country = serializers.SerializerMethodField()

    def get_currency_country(self, organization: Organization):
        currency_country = organization.currency.countries.first()
        return CountrySerializer(currency_country).data

    def get_permissions(self, organization: Organization):
        if self.context['request'].user.is_anonymous:
            return None
        return OrganizationService.get_user_permissions_dict(organization=organization,
                                                             user=self.context['request'].user)

    def get_subscribers(self, organization: Organization):
        return SubscriptionService.get_number_of_subscriptions(organization=organization)

    def get_discounts(self, organization: Organization):
        discounts = DiscountCardService.get_grouped_discounts(organization_id=organization.id)
        return DiscountGroupSerializer(discounts).data

    def get_is_subscribed(self, organization: Organization):
        if self.context['request'].user.is_anonymous:
            return
        return SubscriptionService.is_subscribed(organization=organization, user=self.context['request'].user)

    def get_client_status(self, organization: Organization):
        if self.context['request'].user.is_anonymous:
            return
        data = OrganizationClientFinancialStatusService.get_client_financial_status_data(
            client=self.context['request'].user, organization=organization
        )
        return data

    def get_partners(self, organization: Organization):
        count, partners = OrganizationService.get_partners_dict(organization=organization)
        return {
            'count': count,
            'list': OrganizationWithImageSerializer(partners, many=True).data
        }

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'image', 'subscribers', 'description', 'show_contacts', 'opens_at', 'closes_at',
            'currency', 'currency_country', 'country', 'city', 'address', 'full_location',
            'types', 'phone_numbers', 'social_contacts', 'discounts',
            'is_subscribed', 'permissions', 'client_status', 'partners', 'is_deleted'
        )


class OrganizationListSerializer(serializers.ModelSerializer):
    image = ImageSerializer(many=False)
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
            'title', 'description', 'image_id', 'currency', 'country', 'city',
            'opens_at', 'closes_at', 'address', 'longitude', 'latitude',
            'types', 'numbers', 'accounts', 'cards'
        )

    def validate(self, attrs):
        attrs['owner'] = self.context['request'].user
        return attrs


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField()
    longitude = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)

    class Meta:
        model = Organization
        fields = ('title', 'image_id', 'longitude', 'latitude', 'description', 'types',
                  'opens_at', 'closes_at', 'address', 'currency', 'show_contacts', 'country', 'city',)


class MessageSerializer(serializers.ModelSerializer):
    receivers = serializers.SerializerMethodField()
    receivers_count = serializers.SerializerMethodField()
    receiver_partners = serializers.SerializerMethodField()
    receiver_partner_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id', 'content', 'message_to', 'created_at', 'receivers_count', 'receivers', 'receiver_partners',
            'receiver_partner_count')

    def get_receivers(self, obj):
        receivers = Message.objects.get(id=obj.id).receivers.all()[0:3]
        return UserShortInfoSerializer(receivers, many=True).data

    def get_receivers_count(self, obj):
        return Message.objects.get(id=obj.id).receivers.count()

    def get_receiver_partners(self, obj):
        partners = Message.objects.get(id=obj.id).receiver_partners.all()[0:3]
        return OrganizationWithImageSerializer(partners, many=True).data

    def get_receiver_partner_count(self, obj):
        return Message.objects.get(id=obj.id).receiver_partners.count()


class OrgMessageSerializer(MessageSerializer):
    sender = UserShortInfoSerializer()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id', 'sender', 'message_to', 'content', 'created_at', 'receivers_count', 'receivers', 'sender_role',
            'receiver_partner_count', 'receiver_partners')

    def get_sender_role(self, obj):
        try:
            membership = Membership.objects.get(organization=obj.organization, user=obj.sender)
            return membership.role.title
        except Membership.DoesNotExist:
            return None


class SubscriptionsMessageSerializer(MessageSerializer):
    organization = OrganizationWithImageSerializer(many=False)

    class Meta:
        model = Message
        fields = (
            'id', 'content', 'message_to', 'organization', 'organization_address', 'created_at', 'receivers_count',
            'receivers', 'receiver_partner_count', 'receiver_partners')


class OrgMessageCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=800)

    class Meta:
        model = Message
        fields = ('content', 'message_to')


class OrganizationBannerInfo(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    max_discount = serializers.SerializerMethodField()

    def get_max_discount(self, organization: Organization) -> int:
        return DiscountCardService.get_max_discount(organization=organization)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'max_discount', 'types', 'image',)


class OrganizationTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'title')


class OrganizationTitleImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image')


class OrganizationNotificationInfo(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'address')


class OrganizationUserTransactionSerializer(OrganizationNotificationInfo):
    types = OrganizationTypeSerializer(many=True)
    partners = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'address', 'image', 'types', 'partners')

    def get_partners(self, organization: Organization):
        count, partners = OrganizationService.get_partners_dict(organization=organization)
        return {
            'count': count,
            'list': OrganizationWithImageSerializer(partners, many=True).data
        }
