import re

from decimal import Decimal
from typing import Optional

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.models import File
from common.serializers import ImageSerializer, CountrySerializer, CitySerializer
from organizations.models import (
    PhoneNumber, SocialNetworkContact, Organization, Message, Membership, InstagramIntegration,
    OrganizationVerificationUsers, OrganizationComplaint, OrganizationBlacklist, BlockedUser
)
from organizations.serializers.card_serializers import DiscountGroupSerializer, DiscountCardSerializer
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_promo_services import OrganizationPromoService
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from transactions.models import Transaction
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
        if 'request' in self.context:
            user = self.context['request'].user
            return OrganizationService.get_user_role_in_organization(organization=organization, user=user)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'role', 'description', 'image_id',
                  'opens_at', 'closes_at', 'show_contacts', 'types', 'full_location', 'address', 'verification_status')
        read_only_fields = ['verification_status']


class OrganizationBlacklistSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationBlacklist
        fields = ['organization']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs


class BlockedUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockedUser
        fields = ['id', 'user', 'organization']

    def validate(self, attrs):
        organization_id = attrs['organization'].id
        user_id = self.context['request'].user.id
        try:
            organization = Organization.objects.get(id=organization_id)
            if organization.owner.id != user_id:
                raise NotAcceptableException(_('No rights to edit organization'))
        except Organization.DoesNotExist:
            raise ObjectNotFoundException(_('Organization not found'))

        return attrs


class OrganizationComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationComplaint
        fields = ('organization', 'reason',)

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs


class OrganizationWithImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'verification_status')
        read_only_fields = ['verification_status']


class OrganizationWithTypeImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types', 'verification_status')
        read_only_fields = ['verification_status']


class ItemFeedOrganizationSerializer(OrganizationWithTypeImageSerializer):
    promo_cashback = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    phone_numbers = OrgPhoneNumberSerializer(many=True)

    def get_promo_cashback(self, organization: Organization) -> Optional[Decimal]:
        return OrganizationPromoService.get_available_promo_cashback_amount(organization=organization)

    def get_permissions(self, organization: Organization):
        if self.context['request'].user.is_anonymous:
            return None
        return OrganizationService.get_user_permissions_dict(organization=organization,
                                                             user=self.context['request'].user)

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'image', 'currency', 'promo_cashback', 'types', 'phone_numbers', 'permissions',
            'verification_status', 'is_private'
        )
        read_only_fields = ['verification_status']


class OrganizationShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'title', 'verification_status')
        read_only_fields = ['verification_status']


class PartnerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    partners = serializers.SerializerMethodField()

    def get_partners(self, organization: Organization):
        count, partners = OrganizationService.get_partners_dict(organization=organization)
        return {
            'count': count,
            'list': OrganizationWithImageSerializer(partners, many=True,
                                                    context={'request': self.context.get('request')}).data
        }

    class Meta:
        model = Organization
        fields = ('id', 'title', 'address', 'image', 'types', 'partners', 'verification_status')
        read_only_fields = ['verification_status']


class PartnerWithLatestTransactionSerializer(PartnerSerializer):
    latest_transaction_time = serializers.SerializerMethodField()

    def get_latest_transaction_time(self, organization: Organization):
        # Annotated field
        return organization.latest_transaction_time

    class Meta:
        model = Organization
        fields = ('id', 'title', 'address', 'latest_transaction_time', 'image', 'types', 'partners',
                  'verification_status')
        read_only_fields = ['verification_status']


class PartnerWithLatestTransactionUnprocessedTransactionCountSerializer(PartnerSerializer):
    latest_transaction_time = serializers.SerializerMethodField()
    unprocessed_transaction_count = serializers.SerializerMethodField()

    def get_latest_transaction_time(self, organization: Organization):
        # Annotated field
        return organization.latest_transaction_time

    def get_unprocessed_transaction_count(self, organization: Organization):
        return Transaction.objects.filter(organization=organization, status=Transaction.IN_PROGRESS,
                                          type=Transaction.ONLINE).count()

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'address', 'latest_transaction_time', 'unprocessed_transaction_count', 'image', 'types',
            'partners', 'verification_status')
        read_only_fields = ['verification_status']


class HomepagePartnerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    partners = serializers.SerializerMethodField()

    def get_partners(self, organization: Organization):
        partners = OrganizationService.get_organization_partners(organization=organization)
        return OrganizationWithImageSerializer(partners, many=True).data

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types', 'partners', 'verification_status')
        read_only_fields = ['verification_status']


class OrganizationDetailedSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    permissions = serializers.SerializerMethodField()
    types = OrganizationTypeSerializer(many=True)
    phone_numbers = OrgPhoneNumberSerializer(many=True)
    social_contacts = OrgSocialNetworkContactSerializer(many=True)
    subscribers = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    promo_cashback = serializers.SerializerMethodField()
    client_status = serializers.SerializerMethodField()
    partners = serializers.SerializerMethodField()
    country = CountrySerializer()
    city = CitySerializer()
    currency_country = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    is_adult_content = serializers.SerializerMethodField()
    time_working = serializers.CharField(read_only=True)
    need_add_item = serializers.SerializerMethodField(read_only=True)
    switcher = serializers.CharField()
    is_blacklist = serializers.SerializerMethodField(default=False, read_only=True)

    def get_is_adult_content(self, organization: Organization):
        has_adults_item = bool(organization.shop_items.filter(subcategory__category__is_adult=True).count())
        has_adult_org_type = bool(organization.types.filter(is_adult=True).count())
        if has_adults_item or has_adult_org_type:
            return True
        return False

    def get_address(self, organization: Organization):
        if not organization.address:
            return ""
        return organization.address

    def get_currency_country(self, organization: Organization):
        currency_country = organization.currency.countries.first()
        return CountrySerializer(currency_country).data

    def get_permissions(self, organization: Organization):
        if 'request' in self.context:
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
        if 'request' in self.context:
            if self.context['request'].user.is_anonymous:
                return
            return SubscriptionService.is_subscribed(organization=organization, user=self.context['request'].user)

    def get_promo_cashback(self, organization: Organization) -> Optional[Decimal]:
        return OrganizationPromoService.get_available_promo_cashback_amount(organization=organization)

    def get_client_status(self, organization: Organization):
        if 'request' in self.context:
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

    def get_need_add_item(self, obj):
        if self.context.get("need_add_item"):
            return True
        return False

    def get_is_blacklist(self, organization: Organization):
        if 'request' in self.context:
            user = self.context['request'].user
            return OrganizationBlacklist.objects.filter(organization_id=organization.id, user_id=user.id).exists()

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'title_lang', 'image', 'subscribers', 'description', 'description_lang', 'show_contacts',
            'opens_at', 'closes_at', 'currency', 'currency_country', 'country', 'city', 'address',
            'full_location', 'types', 'phone_numbers', 'social_contacts', 'discounts', 'has_delivery',
            'has_self_pick_up', 'promo_cashback', 'is_subscribed', 'permissions', 'client_status', 'partners',
            'is_deleted', 'is_delivery_service', 'is_adult_content', 'time_working', 'is_banned', 'is_private',
            'verification_status', 'avg_check', 'need_add_item', 'switcher', 'is_blacklist'
        )
        read_only_fields = ['verification_status', 'need_add_item']


class OrganizationListSerializer(serializers.ModelSerializer):
    image = ImageSerializer(many=False)
    role = serializers.SerializerMethodField()

    def get_role(self, organization: Organization):
        user = self.context['request'].user
        return OrganizationService.get_user_role_in_organization(organization=organization, user=user)

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'is_deleted', 'is_private', 'is_banned', 'verification_status', 'image', 'role', 'is_delivery_service', 'verification_status', 'avg_check')
        read_only_fields = ['verification_status']


class OrganizationCreateSerializer(serializers.ModelSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all()
    )
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
            'types', 'numbers', 'accounts', 'cards', 'verification_status', 'avg_check'
        )
        read_only_fields = ['verification_status']

    def validate(self, attrs):
        attrs['owner'] = self.context['request'].user
        return attrs


class OrganizationGoogleMapsCreateSerializer(serializers.Serializer):
    google_maps_url = serializers.URLField()

    def validate_google_maps_url(self, value):
        pattern = r'^(https:\/\/goo\.gl\/maps\/[a-zA-Z0-9]+)|(https:\/\/maps\.app\.goo\.gl\/[a-zA-Z0-9\?=_-]+)$'

        if not re.match(pattern, value):
            raise serializers.ValidationError(_("Invalid Google Maps URL"))

        return value


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField()
    longitude = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)

    class Meta:
        model = Organization
        fields = ('title', 'image_id', 'longitude', 'latitude', 'description', 'types',
                  'opens_at', 'closes_at', 'address', 'currency', 'show_contacts', 'country', 'city',
                  'verification_status', 'avg_check', 'is_private', 'switcher')
        read_only_fields = ['verification_status']


class DeliverySettingsUpdateSerializer(serializers.ModelSerializer):
    has_delivery = serializers.BooleanField(required=True, allow_null=False)
    has_self_pick_up = serializers.BooleanField(required=True, allow_null=False)

    class Meta:
        model = Organization
        fields = ('has_delivery', 'has_self_pick_up',)

    def validate(self, attrs):
        if not attrs['has_delivery'] and not attrs['has_self_pick_up']:
            raise NotAcceptableException(_('Should have at least one enabled delivery option'))
        return attrs


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
        return UserShortInfoSerializer(
            receivers,
            many=True,
            context={"request": self.context.get("request")}
        ).data

    def get_receivers_count(self, obj):
        return Message.objects.get(id=obj.id).receivers.count()

    def get_receiver_partners(self, obj):
        partners = Message.objects.get(id=obj.id).receiver_partners.all()[0:3]
        return OrganizationWithImageSerializer(
            partners,
            many=True,
            context={"request": self.context.get("request")}
        ).data

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
    content = serializers.CharField(max_length=2000)

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
        fields = ('id', 'title', 'max_discount', 'types', 'image', 'verification_status', 'avg_check')
        read_only_fields = ['verification_status']


class OrganizationShortInfoWithCurrencySerializer(serializers.ModelSerializer):
    types = OrganizationTypeSerializer(many=True)
    image = ImageSerializer()
    time_working = serializers.CharField(read_only=True)
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, organization: Organization):
        if self.context['request'].user.is_anonymous:
            return None
        return OrganizationService.get_user_permissions_dict(organization=organization,
                                                             user=self.context['request'].user)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'currency', 'types', 'image', 'address', 'time_working', 'has_delivery',
                  'has_self_pick_up', 'verification_status', 'avg_check', 'permissions'
                  )
        read_only_fields = ['verification_status']


class OrganizationInCartDetailsSerializer(OrganizationShortInfoWithCurrencySerializer):
    time_working = serializers.CharField(read_only=True)

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'currency', 'types', 'image', 'address', 'has_delivery', 'has_self_pick_up',
            'opens_at', 'closes_at', 'time_working', 'verification_status', 'avg_check'
        )
        read_only_fields = ['verification_status']


class OrganizationInBookingDetailsSerializer(OrganizationShortInfoWithCurrencySerializer):
    time_working = serializers.CharField(read_only=True)
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, organization: Organization):
        if self.context['request'].user.is_anonymous:
            return None
        return OrganizationService.get_user_permissions_dict(organization=organization,
                                                             user=self.context['request'].user)

    class Meta:
        model = Organization
        fields = (
            'id', 'title', 'currency', 'types', 'image', 'address', 'has_delivery', 'has_self_pick_up',
            'opens_at', 'closes_at', 'time_working', 'verification_status', 'avg_check', 'permissions'
        )
        read_only_fields = ['verification_status']


class OrganizationTitleImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'verification_status')
        read_only_fields = ['verification_status']


class OrganizationTitleImageCurrencySerializer(OrganizationTitleImageSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'title', 'currency', 'image', 'verification_status')
        read_only_fields = ['verification_status']


class OrganizationNotificationInfo(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'address', 'verification_status')
        read_only_fields = ['verification_status']


class OrganizationUserTransactionSerializer(OrganizationNotificationInfo):
    types = OrganizationTypeSerializer(many=True)
    partners = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ('id', 'title', 'address', 'image', 'types', 'partners', 'verification_status')
        read_only_fields = ['verification_status']

    def get_partners(self, organization: Organization):
        count, partners = OrganizationService.get_partners_dict(organization=organization)
        return {
            'count': count,
            'list': OrganizationWithImageSerializer(partners, many=True).data
        }


class OrganizationTitleSerializer(OrganizationUserTransactionSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'title', 'description',
                  'currency', 'address', 'image', 'types', 'partners', 'is_delivery_service', 'verification_status')
        read_only_fields = ['verification_status']


class InstagramIntegrationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramIntegration
        fields = ('url',)


class InstagramIntegrationUserProfile(serializers.ModelSerializer):
    full_name = serializers.CharField(source='account_full_name')
    profile_image = serializers.ImageField(source='avatar.medium', allow_null=True)

    class Meta:
        model = InstagramIntegration
        fields = ('full_name', 'profile_image',)


class InstagramIntegrationLinkSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = InstagramIntegration
        fields = ('id', 'url', 'user_profile')

    def get_user_profile(self, obj: InstagramIntegration):
        return InstagramIntegrationUserProfile(obj, context=self.context).data


class OrgVerificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationVerificationUsers
        fields = ('username', 'phone_number', 'email')
