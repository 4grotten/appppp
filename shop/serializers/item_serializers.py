import calendar
import datetime
import ast

from django.db import transaction
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import Point
from rest_framework import serializers

from organizations.services.membership_services import MembershipService
from users.models import User
from common.exceptions import NotAcceptableException
from common.models import File, FileVideo, Currency, Country, City
from common.serializers import ImageSerializer, VideoSerializer, CountryResumeSerializer, CityResumeSerializer
from organizations.models import HotlinkCollectionItem, Organization, BlockedUser, Role, Membership
from organizations.serializers.organization_serializers import ItemFeedOrganizationSerializer, \
    OrganizationTitleImageSerializer, OrganizationNotificationInfo
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, ItemInstagramData, RentalPeriod, Booking, TicketPeriod, Ticket, ResumeInfo, \
    ResumeInfoFile, ResumePhoneNumber, ResumeSocialNetwork, ResumeDetailInfo, ResumeWorkExperience, Education, \
    ResumeEducation, ResumeRequest
from shop.serializers.category_serializers import ItemSubcategoryBriefSerializer
from shop.services.cart_services import CartItemService
from shop.services.like_bookmark_services import LikeService, BookmarkService
from stock.models import ShopItemSizeCount
from stock.serializers import SizeFormatByItemSerializer, ShopItemSizeCountSerializer, SubcategorySerializer
from transactions.models import Transaction
from users.serializers import UserInfoSerializer, ProfileSerializer


class ItemSetRetrieveSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    currency = serializers.CharField(source='organization.currency')
    has_in_stock = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_image(self, item: ShopItem):
        image = item.images.first()
        thumbnail = item.videos.first()
        if image:
            image = File.objects.get(id=image.id)
            return ImageSerializer(image, context=self.context).data
        else:
            thumbnail = FileVideo.objects.get(id=thumbnail.id)
            return VideoSerializer(thumbnail, context=self.context).data

    class Meta:
        model = ShopItem
        fields = ('id', 'price', 'discount', 'currency', 'image', 'has_in_stock')


class RentItemsPeriodSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(input_formats=['%d.%m.%Y',], format="%d.%m.%Y")
    end_date = serializers.DateField(input_formats=['%d.%m.%Y',], format="%d.%m.%Y")
    start_time = serializers.DateTimeField(input_formats=['%H:%M'], format="%H:%M")
    end_time = serializers.DateTimeField(input_formats=['%H:%M'], format="%H:%M")

    class Meta:
        model = RentalPeriod
        fields = (
            'id', 'rent_time_type', 'start_date', 'end_date', 'start_time', 'end_time'
        )


class TicketPeriodSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(input_formats=['%d.%m.%Y',], format="%d.%m.%Y")
    end_date = serializers.DateField(input_formats=['%d.%m.%Y',], format="%d.%m.%Y")
    start_time = serializers.DateTimeField(input_formats=['%H:%M'], format="%H:%M")
    end_time = serializers.DateTimeField(input_formats=['%H:%M'], format="%H:%M")

    class Meta:
        model = TicketPeriod
        fields = (
            'id', 'start_date', 'end_date', 'start_time', 'end_time'
        )


class ResumeInfoUpdateSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(purchase_type=ShopItem.RESUME))

    class Meta:
        model = ResumeInfo
        fields = ('id', 'item', 'gender', 'full_name', 'date_of_birth', 'languages', 'files')


class ResumePhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumePhoneNumber
        fields = ('id', 'phone_number')


class ResumePhoneNumberUpdateSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(purchase_type=ShopItem.RESUME))
    phone_numbers = serializers.ListSerializer(child=serializers.CharField())


class ResumeSocialNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeSocialNetwork
        fields = ('id', 'url')


class ResumeSocialNetworkUpdateSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(purchase_type=ShopItem.RESUME))
    urls = serializers.ListSerializer(child=serializers.CharField())


class ResumeDetailInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeDetailInfo
        fields = ('id', 'text')


class ResumeDetailInfoUpdateSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(purchase_type=ShopItem.RESUME))
    text = serializers.CharField()


class ResumeWorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeWorkExperience
        fields = ('id', 'company_name', 'position', 'text', 'start_of_work', 'end_of_work', 'up_to_now')


class ResumeWorkExperienceUpdateSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(purchase_type=ShopItem.RESUME))
    work_experiences = serializers.ListSerializer(
        child=ResumeWorkExperienceSerializer()
    )


class ResumeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeEducation
        fields = ('id', 'school_name', 'category', 'text', 'start_of_study', 'end_of_study', 'up_to_now')


class ResumeEducationUpdateSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.filter(purchase_type=ShopItem.RESUME))
    educations = serializers.ListSerializer(
        child=ResumeEducationSerializer()
    )


class ResumeInfoFileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ResumeInfoFile
        fields = ('id', 'file', 'name')
        read_only_fields = ('name',)

    def get_name(self, obj):
        return obj.file.name.split("/")[-1]


class ResumeInfoSerializer(serializers.ModelSerializer):
    files = ResumeInfoFileSerializer(many=True)
    contact_filled = serializers.SerializerMethodField()
    social_network_filled = serializers.SerializerMethodField()
    detail_info_filled = serializers.SerializerMethodField()
    work_experience_filled = serializers.SerializerMethodField()
    education_filled = serializers.SerializerMethodField()

    class Meta:
        model = ResumeInfo
        fields = ('id', 'gender', 'full_name', 'date_of_birth', 'languages', 'files', 'contact_filled',
                  'social_network_filled', 'detail_info_filled', 'work_experience_filled', 'education_filled')


    def get_contact_filled(self, resume_info: ResumeInfo):
        return resume_info.item.resume_phone_numbers.exists()

    def get_social_network_filled(self, resume_info: ResumeInfo):
        return resume_info.item.resume_social_networks.exists()

    def get_detail_info_filled(self, resume_info: ResumeInfo):
        return hasattr(resume_info.item, 'resume_detail_info') and resume_info.item.resume_detail_info is not None

    def get_work_experience_filled(self, resume_info: ResumeInfo):
        return resume_info.item.resume_work_experience.exists()

    def get_education_filled(self, resume_info: ResumeInfo):
        return resume_info.item.resume_education.exists()


class EducationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Education
        fields = ('id', 'name')


class ItemRetrieveSerializer(serializers.ModelSerializer):
    organization = ItemFeedOrganizationSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)
    videos = VideoSerializer(many=True)
    instagram_data = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()
    rental_period = RentItemsPeriodSerializer()
    ticket_period = TicketPeriodSerializer()
    citizenship = CountryResumeSerializer(many=True)
    education = EducationSerializer(many=True)
    current_locations = serializers.SerializerMethodField()
    preferred_locations = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True, context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None)
        images = ItemInstagramData.objects.filter(item=item, video_url=None).order_by('pk')
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)

    def get_is_liked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return LikeService.is_item_liked_by_user(item=item, user=user)

    def get_is_bookmarked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return BookmarkService.is_item_bookmarked_by_user(item=item, user=user)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    def get_comment_count(self, item: ShopItem) -> int:
        return item.comments.count()

    def get_can_comment(self, item: ShopItem) -> bool:
        if self.context['request'].user:
            user = self.context['request'].user
            blocked_users = BlockedUser.objects.filter(organization_id=item.organization.id, user=user.id).values_list('user_id', flat=True).distinct()
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()

    def get_current_locations(self, item: ShopItem):
        current_locations_list = []
        current_locations = item.current_locations
        if current_locations and isinstance(current_locations, list):
            for location_code in current_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    current_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        current_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return current_locations_list

    def get_preferred_locations(self, item: ShopItem):
        preferred_locations_list = []
        preferred_locations = item.preferred_locations
        if preferred_locations and isinstance(preferred_locations, list):
            for location_code in preferred_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    preferred_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        preferred_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return preferred_locations_list


    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount',
            'instagram_link', 'is_published', 'is_hidden', 'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'can_comment', 'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'instagram_data', 'is_updated', 'available_sizes', 'set_items', 'has_in_stock', 'purchase_type',
            'rental_period', 'ticket_period', 'address', 'full_location', 'minimum_purchase', 'currency', 'salary_from',
            'salary_to', 'citizenship', 'current_locations', 'preferred_locations', 'links', 'education'
        )


class ItemRentalRetrieveSerializer(serializers.ModelSerializer):
    organization = ItemFeedOrganizationSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)
    videos = VideoSerializer(many=True)
    instagram_data = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()
    rental_period = RentItemsPeriodSerializer()
    ticket_period = TicketPeriodSerializer()


    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True, context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None)
        images = ItemInstagramData.objects.filter(item=item, video_url=None).order_by('pk')
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)

    def get_is_liked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return LikeService.is_item_liked_by_user(item=item, user=user)

    def get_is_bookmarked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return BookmarkService.is_item_bookmarked_by_user(item=item, user=user)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    def get_comment_count(self, item: ShopItem) -> int:
        return item.comments.count()

    def get_can_comment(self, item: ShopItem) -> bool:
        if self.context['request'].user:
            user = self.context['request'].user
            blocked_users = BlockedUser.objects.filter(organization_id=item.organization.id, user=user.id).values_list('user_id', flat=True).distinct()
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()


    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount',
            'instagram_link', 'is_published', 'is_hidden', 'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'can_comment', 'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'instagram_data', 'is_updated', 'available_sizes', 'set_items', 'has_in_stock', 'purchase_type', 'address',
            'full_location', 'rental_period', 'ticket_period', 'purchase_type'
        )


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    longitude = serializers.FloatField(allow_null=True, required=False)
    latitude = serializers.FloatField(allow_null=True, required=False)
    rental_period = RentItemsPeriodSerializer(required=False)
    ticket_period = TicketPeriodSerializer(required=False)
    citizenship = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), many=True, required=False)
    education = serializers.PrimaryKeyRelatedField(queryset=Education.objects.all(), many=True, required=False)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'name_lang', 'description', 'description_lang',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'videos', 'youtube_links',
            'is_updated', 'removed_at', 'purchase_type', 'address', 'rental_period', 'ticket_period', 'full_location',
            'longitude', 'latitude', 'minimum_purchase', 'currency', 'salary_from', 'salary_to', 'citizenship',
            'current_locations', 'preferred_locations', 'links', 'education'
        )
        read_only_fields = ['name_lang', 'description_lang']

    def validate(self, attrs):
        user = self.context['request'].user
        organization = attrs['organization']

        subcategory = attrs.get('subcategory', None)
        subcategory_organization = getattr(subcategory, 'organization', None)
        if subcategory_organization is not None and not subcategory_organization == organization:
            raise NotAcceptableException(_('Organization does not have this subcategory'))

        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException(_('No rights to edit organization'))

        return attrs

    def update(self, instance, validated_data):
        rental_period_data = validated_data.pop('rental_period', None)
        if rental_period_data:
            rental_period = instance.rental_period
            rental_period_serializer = RentItemsPeriodSerializer(rental_period, data=rental_period_data, partial=True)
            if rental_period_serializer.is_valid(raise_exception=True):
                rental_period_serializer.save()

        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if longitude and latitude:
            point = Point(longitude, latitude)
        else:
            point = None
        instance.location = point
        instance.save()

        validated_data.pop('organization', None)
        if 'price' in validated_data and validated_data.get('price') is None:
            CartItemService.delete_item_from_all_carts(self.instance)

        return super().update(instance, validated_data)

    def save(self, **kwargs):
        images = self.validated_data.get('images', [])
        for index, image in enumerate(images):
            image.order = index
            image.save(update_fields=('order',))

        videos = self.validated_data.get('videos', [])
        for index, video in enumerate(videos):
            video.order = index
            video.save(update_fields=('order',))

        longitude = self.validated_data.pop('longitude', None)
        latitude = self.validated_data.pop('latitude', None)

        if longitude and latitude:
            point = Point(longitude, latitude)
        else:
            point = None

        instance = super().save(**kwargs)
        instance.location = point
        instance.save()

        if instance.article == '' or instance.article is None:
            instance.article = f"ART{instance.id}"
            instance.save(update_fields=('article',))

        if self.validated_data.get('price') == 0.00:
            instance.price = None
            instance.save()

        organization_data = self.validated_data.get('organization')
        Organization.objects.filter(id=organization_data.id).update(add_item_date=datetime.datetime.now())

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('latitude', None)
        representation.pop('longitude', None)
        return representation


class UserItemCreateUpdateSerializer(serializers.ModelSerializer):
    longitude = serializers.FloatField(allow_null=True, required=False)
    latitude = serializers.FloatField(allow_null=True, required=False)
    rental_period = RentItemsPeriodSerializer(required=False)
    ticket_period = TicketPeriodSerializer(required=False)
    citizenship = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), many=True, required=False)
    education = serializers.PrimaryKeyRelatedField(queryset=Education.objects.all(), many=True, required=False)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'user', 'organization', 'subcategory',
            'name', 'name_lang', 'description', 'description_lang',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'videos', 'youtube_links',
            'is_updated', 'removed_at', 'purchase_type', 'address', 'rental_period', 'ticket_period', 'full_location',
            'longitude', 'latitude', 'minimum_purchase', 'currency', 'salary_from', 'salary_to', 'citizenship',
            'current_locations', 'preferred_locations', 'links', 'education'
        )
        read_only_fields = ['name_lang', 'description_lang']

    def validate(self, attrs):
        user = self.context['request'].user
        max_items_for_user = 3

        existing_items_count = ShopItem.objects.filter(user=user, purchase_type=ShopItem.RESUME).count()
        if existing_items_count >= max_items_for_user:
            raise NotAcceptableException(_('Maximum allowed resumes for user reached'))

        return attrs

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if longitude and latitude:
            point = Point(longitude, latitude)
        else:
            point = None
        instance.location = point
        instance.save()

        return super().update(instance, validated_data)

    def save(self, **kwargs):
        images = self.validated_data.get('images', [])
        for index, image in enumerate(images):
            image.order = index
            image.save(update_fields=('order',))

        videos = self.validated_data.get('videos', [])
        for index, video in enumerate(videos):
            video.order = index
            video.save(update_fields=('order',))

        longitude = self.validated_data.pop('longitude', None)
        latitude = self.validated_data.pop('latitude', None)

        if longitude and latitude:
            point = Point(longitude, latitude)
        else:
            point = None

        instance = super().save(**kwargs)
        user = self.validated_data.get('user', None)
        if user:
            organization = Organization.objects.filter(types__is_resume=True).first()
            if organization:
                instance.organization = organization
                instance.save(update_fields=('organization',))

                role, created = Role.objects.get_or_create(
                    title='Vacancy Publisher',
                    organization=organization,
                    defaults={
                        'can_sale': False,
                        'can_check_attendance': False,
                        'can_see_stats': False,
                        'can_edit_organization': False,
                        'can_send_message': True,
                        'can_edit_partner': False,
                        'can_deliver': False,
                        'can_edit_own_resume': True
                    }
                )
                is_employee = Membership.objects.filter(organization=organization, user=user, role=role).exists()
                if not is_employee and user != organization.owner:
                    MembershipService.add_employee_to_resume_org(organization=organization, employee=user, role=role,
                                                             added_by=organization.owner)
        instance.location = point
        instance.save()

        if instance.article == '' or instance.article is None:
            instance.article = f"ART{instance.id}"
            instance.save(update_fields=('article',))

        if self.validated_data.get('price') == 0.00:
            instance.price = None
            instance.save()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('latitude', None)
        representation.pop('longitude', None)
        return representation


class ItemChangePublishedSerializer(serializers.Serializer):
    is_published = serializers.BooleanField()
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())


class ItemInstagramVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    def get_thumbnail(self, obj):
        return obj.thumbnail_url

    class Meta:
        model = ItemInstagramData
        fields = (
            'thumbnail', 'video_url'
        )


class ItemInstagramImageSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    large = serializers.SerializerMethodField()
    small = serializers.SerializerMethodField()
    medium = serializers.SerializerMethodField()

    def get_file(self, obj):
        return obj.thumbnail_url

    def get_large(self, obj):
        return obj.thumbnail_url

    def get_small(self, obj):
        return obj.thumbnail_url

    def get_medium(self, obj):
        return obj.thumbnail_url

    class Meta:
        model = ItemInstagramData
        fields = (
            'file', 'large', 'small', 'medium'
        )


class ItemsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang',
            'price', 'is_published', 'updated_at', 'images'
        )


class ItemListSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()
    is_bookmarked = serializers.BooleanField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    instagram_data = serializers.SerializerMethodField()

    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None).order_by('created_at')
        images = ItemInstagramData.objects.filter(item=item, video_url=None).order_by('created_at')
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    def get_comment_count(self, item: ShopItem) -> int:
        return item.comments.count()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount', 'instagram_link', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images',
            'instagram_data', 'is_updated'
        )
        read_only_fields = ['name_lang', 'description_lang']


class SubscriptionItemSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()
    videos = VideoSerializer(many=True)
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()
    rental_period = RentItemsPeriodSerializer()
    ticket_period = TicketPeriodSerializer()
    citizenship = CountryResumeSerializer(many=True)
    education = EducationSerializer(many=True)
    current_locations = serializers.SerializerMethodField()
    preferred_locations = serializers.SerializerMethodField()
    own_resume = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True,
                                               context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    def get_current_locations(self, item: ShopItem):
        current_locations_list = []
        current_locations = item.current_locations
        if current_locations and isinstance(current_locations, list):
            for location_code in current_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    current_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        current_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return current_locations_list

    def get_preferred_locations(self, item: ShopItem):
        preferred_locations_list = []
        preferred_locations = item.preferred_locations
        if preferred_locations and isinstance(preferred_locations, list):
            for location_code in preferred_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    preferred_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        preferred_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return preferred_locations_list

    def get_own_resume(self, item: ShopItem):
        user = self.context['request'].user
        if item.user == user:
            return True
        return False

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount', 'instagram_link', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'instagram_data', 'is_updated', 'available_sizes', 'set_items', 'has_in_stock', 'rental_period',
            'ticket_period', 'full_location', 'purchase_type', 'address', 'minimum_purchase', 'currency', 'salary_from',
            'salary_to', 'citizenship', 'education', 'current_locations', 'preferred_locations', 'links', 'own_resume'
        )
        read_only_fields = ['name_lang', 'description_lang']


class ItemFeedSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    videos = VideoSerializer(many=True)
    subcategory = ItemSubcategoryBriefSerializer()
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)
    rental_period = RentItemsPeriodSerializer()
    ticket_period = TicketPeriodSerializer()
    citizenship = CountryResumeSerializer(many=True)
    education = EducationSerializer(many=True)
    current_locations = serializers.SerializerMethodField()
    preferred_locations = serializers.SerializerMethodField()
    own_resume = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True,
                                               context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    def get_can_comment(self, item: ShopItem) -> bool:
        if self.context['request'].user:
            user = self.context['request'].user
            blocked_users = BlockedUser.objects.filter(organization_id=item.organization.id, user=user.id).values_list('user_id', flat=True).distinct()
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()

    def get_current_locations(self, item: ShopItem):
        current_locations_list = []
        current_locations = item.current_locations
        if current_locations and isinstance(current_locations, list):
            for location_code in current_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    current_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        current_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return current_locations_list

    def get_preferred_locations(self, item: ShopItem):
        preferred_locations_list = []
        preferred_locations = item.preferred_locations
        if preferred_locations and isinstance(preferred_locations, list):
            for location_code in preferred_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    preferred_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        preferred_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return preferred_locations_list

    def get_own_resume(self, item: ShopItem):
        user = self.context['request'].user
        if item.user == user:
            return True
        return False

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount', 'instagram_link', 'is_published', 'is_hidden',
            'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization', 'user',
            'instagram_data', 'is_updated', 'comment_count', 'can_comment', 'available_sizes', 'set_items',
            'has_in_stock', 'rental_period', 'ticket_period', 'purchase_type', 'full_location', 'address',
            'minimum_purchase', 'currency', 'salary_from', 'salary_to', 'citizenship', 'education', 'current_locations',
            'preferred_locations', 'links', 'own_resume'
        )
        read_only_fields = ['name_lang', 'description_lang']


class ResumeFeedSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    videos = VideoSerializer(many=True)
    subcategory = ItemSubcategoryBriefSerializer()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)
    citizenship = CountryResumeSerializer(many=True)
    education = EducationSerializer(many=True)
    current_locations = serializers.SerializerMethodField()
    preferred_locations = serializers.SerializerMethodField()
    own_resume = serializers.SerializerMethodField()

    def get_is_liked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return LikeService.is_item_liked_by_user(item=item, user=user)

    def get_is_bookmarked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return BookmarkService.is_item_bookmarked_by_user(item=item, user=user)

    def get_can_comment(self, item: ShopItem) -> bool:
        if self.context['request'].user:
            user = self.context['request'].user
            blocked_users = BlockedUser.objects.filter(organization_id=item.organization.id, user=user.id).values_list('user_id', flat=True).distinct()
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()

    def get_current_locations(self, item: ShopItem):
        current_locations_list = []
        current_locations = item.current_locations
        if current_locations and isinstance(current_locations, list):
            for location_code in current_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    current_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        current_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return current_locations_list

    def get_preferred_locations(self, item: ShopItem):
        preferred_locations_list = []
        preferred_locations = item.preferred_locations
        if preferred_locations and isinstance(preferred_locations, list):
            for location_code in preferred_locations:
                try:
                    country = Country.objects.get(code=location_code)
                    country_serializer = CountryResumeSerializer(country)
                    preferred_locations_list.append(country_serializer.data)
                except Country.DoesNotExist:
                    try:
                        city = City.objects.get(id=location_code)
                        city_serializer = CityResumeSerializer(city)
                        preferred_locations_list.append(city_serializer.data)
                    except City.DoesNotExist:
                        pass

        return preferred_locations_list

    def get_own_resume(self, item: ShopItem):
        user = self.context['request'].user
        if item.user == user:
            return True
        return False

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'instagram_link', 'is_published', 'is_hidden', 'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization', 'user',
            'instagram_data', 'is_updated', 'comment_count', 'can_comment',
            'purchase_type', 'full_location', 'address', 'currency', 'salary_from', 'salary_to', 'citizenship',
            'education', 'current_locations', 'preferred_locations', 'links', 'own_resume'
        )
        read_only_fields = ['name_lang', 'description_lang']


class StartDateTimeSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(required=False, default=None)


class ItemInCartSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, item: ShopItem) -> dict:
        image = item.images.filter(order=0).first()
        video = item.videos.filter(order=0).first()
        if image:
            return ImageSerializer(image, context=self.context).data
        if video:
            return ImageSerializer(video.thumbnail, context=self.context).data
        image_data = None
        insta_data = ItemInstagramData.objects.filter(item=item, thumbnail_url__isnull=False).first()
        if insta_data is not None:
            item_video_thumbnail_url = insta_data.thumbnail_url
            image_data = {
                "id": 0,
                "file": item_video_thumbnail_url,
                "name": "Cart thumbnail",
                "large": item_video_thumbnail_url,
                "medium": item_video_thumbnail_url,
                "small": item_video_thumbnail_url
            }
        return image_data

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'price', 'discounted_price', 'image', 'minimum_purchase'
        )


class ItemInBookingSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, item: ShopItem) -> dict:
        image = item.images.filter(order=0).first()
        video = item.videos.filter(order=0).first()
        if image:
            return ImageSerializer(image, context=self.context).data
        if video:
            return ImageSerializer(video.thumbnail, context=self.context).data
        image_data = None
        insta_data = ItemInstagramData.objects.filter(item=item, thumbnail_url__isnull=False).first()
        if insta_data is not None:
            item_video_thumbnail_url = insta_data.thumbnail_url
            image_data = {
                "id": 0,
                "file": item_video_thumbnail_url,
                "name": "Cart thumbnail",
                "large": item_video_thumbnail_url,
                "medium": item_video_thumbnail_url,
                "small": item_video_thumbnail_url
            }
        return image_data

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'price', 'discounted_price', 'image'
        )


class ItemInHotlinkSerializer(ItemInCartSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'image'
        )


class ItemInHotlinkCollectionSerializer(ItemInCartSerializer):
    subcategory_name = serializers.CharField(source='subcategory.name', default=None)
    currency = serializers.CharField(source='organization.currency.code')
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'subcategory_name', 'price', 'discounted_price', 'currency', 'is_selected', 'image')

    def get_is_selected(self, item: ShopItem) -> bool:
        if 'hotlink' not in self.context:
            return False
        return HotlinkCollectionItem.objects.filter(hotlink=self.context['hotlink'], item=item).exists()


class ItemRentalYearSerializer(serializers.Serializer):
    value = serializers.CharField()
    is_booked = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ('value', 'is_booked', 'is_available')

    def get_is_available(self, booking: Booking) -> bool:
        year = int(booking['value'])
        current_year = datetime.datetime.now().year

        rental = self.context.get('rental')
        start_year = rental.rental_period.start_date.year
        end_year = rental.rental_period.end_date.year

        if year < current_year:
            return False
        elif year < start_year or year > end_year:
            return False
        return True

    def get_is_booked(self, booking: Booking) -> bool:
        year = int(booking['value'])
        rental = self.context.get('rental')

        bookings = rental.user_bookings.filter(
            start_time__year__lte=year,
            end_time__year__gte=year,
            transaction__is_processed=True
        )
        if bookings.exists():
            for month in range(1, 13):
                bookings_in_month = bookings.filter(
                    start_time__month__lte=month,
                    end_time__month__gte=month
                )
                if not bookings_in_month.exists():
                    return False
            return True
        return False


class ItemRentalMonthSerializer(serializers.Serializer):
    value = serializers.CharField()
    is_booked = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ('value', 'is_available', 'is_booked')

    def get_is_available(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        year = time_query_datetime.year
        value = booking['value']

        value_datetime = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M')
        month = value_datetime.month

        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month

        rental = self.context.get('rental')
        start_year = rental.rental_period.start_date.year
        end_year = rental.rental_period.end_date.year
        start_month = rental.rental_period.start_date.month
        end_month = rental.rental_period.end_date.month


        if year < current_year:
            return False
        elif year < start_year or year > end_year or (year == start_year and month < start_month) or (
                year == end_year and month > end_month):
            return False
        elif year == current_year and month < current_month:
            return False

        return True

    def get_is_booked(self, booking):

        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        year = time_query_datetime.year

        value = booking['value']
        value_datetime = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M')
        month = value_datetime.month

        rental = self.context.get('rental')
        num_days = calendar.monthrange(year, month)[1]
        days = [datetime.datetime(year, month, day).date() for day in range(1, num_days + 1)]
        bookings = rental.user_bookings.filter(
            start_time__year__lte=year,
            end_time__year__gte=year,
            start_time__month__lte=month,
            end_time__month__gte=month,
            transaction__is_processed=True
        )
        if bookings.exists():
            month_booked = False
            for day in days:
                is_day_booked = bookings.filter(
                    start_time__date__lte=day,
                    end_time__date__gte=day
                ).exists()
                if not is_day_booked:
                    month_booked = False
                    break
                month_booked = True

            return month_booked

        return False


class ItemRentalDaySerializer(serializers.Serializer):
    value = serializers.DateField()
    is_booked = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    def get_is_available(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        value = booking['value']

        year = time_query_datetime.year
        month = time_query_datetime.month
        day = value.day

        current_datetime = datetime.datetime.now()
        current_year = current_datetime.year
        current_month = current_datetime.month
        current_day = current_datetime.day

        rental = self.context.get('rental')
        start_year = rental.rental_period.start_date.year
        end_year = rental.rental_period.end_date.year
        start_month = rental.rental_period.start_date.month
        end_month = rental.rental_period.end_date.month
        start_day = rental.rental_period.start_date.day
        end_day = rental.rental_period.end_date.day


        if year < current_year:
            return False
        elif year == current_year and month < current_month:
            return False
        elif year < start_year or year > end_year or (year == start_year and month < start_month) or (
                year == end_year and month > end_month) or (
                year == start_year and month == start_month and day < start_day) or (
                year == end_year and month == end_month and day > end_day):
            return False
        elif year == current_year and month == current_month and day < current_day:
            return False

        return True


    def get_is_booked(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        value = booking['value']
        current_date = value
        rental = self.context.get('rental')
        hours = [hour for hour in range(0, 24)]
        bookings = rental.user_bookings.filter(
            start_time__date__lte=current_date,
            end_time__date__gte=current_date,
            transaction__is_processed=True
        )

        if bookings.exists():
            for hour in hours:
                bookings_in_hour = bookings.filter(
                    start_time__hour__lte=hour,
                    end_time__hour__gte=hour,
                )
                if not bookings_in_hour.exists():
                    return False
            return True
        return False


class ItemRentalHourSerializer(serializers.Serializer):
    value = serializers.DateTimeField(format="%Y-%m-%dT%H:%M")
    is_booked = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()


    def get_is_available(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        value = booking['value']

        year = time_query_datetime.year
        month = time_query_datetime.month
        day = time_query_datetime.day
        hour = value.hour

        current_datetime = datetime.datetime.now()
        current_year = current_datetime.year
        current_month = current_datetime.month
        current_day = current_datetime.day
        current_hour = current_datetime.hour

        rental = self.context.get('rental')
        start_year = rental.rental_period.start_date.year
        end_year = rental.rental_period.end_date.year
        start_month = rental.rental_period.start_date.month
        end_month = rental.rental_period.end_date.month
        start_day = rental.rental_period.start_date.day
        end_day = rental.rental_period.end_date.day
        start_hour = rental.rental_period.start_time.hour
        end_hour = rental.rental_period.end_time.hour

        if year < current_year:
            return False
        elif year == current_year and month < current_month:
            return False
        elif year == current_year and month == current_month and day < current_day:
            return False
        elif year < start_year or year > end_year or (year == start_year and month < start_month) or (
                year == end_year and month > end_month) or (
                year == start_year and month == start_month and day < start_day) or (
                year == end_year and month == end_month and day > end_day) or (
                year == start_year and month == start_month and day == start_day and hour < start_hour) or (
                year == end_year and month == end_month and day == end_day and hour >= end_hour):
            return False
        elif year == current_year and month == current_month and day == current_day and hour < current_hour:
            return False

        return True


    def get_is_booked(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        value = booking['value']
        current_date = time_query_datetime
        current_hour = value.hour

        rental = self.context.get('rental')

        bookings = rental.user_bookings.filter(
            start_time__date=current_date,
            start_time__hour__lte=current_hour,
            end_time__date=current_date,
            end_time__hour__gte=current_hour,
            transaction__is_processed=True
        )

        if bookings.exists():
            for minute in range(0, 60):
                bookings_in_minute = bookings.filter(
                    start_time__minute__lte=minute,
                    end_time__minute__gte=minute
                )
                if not bookings_in_minute.exists():
                    return False
            return True
        return False


class ItemRentalMinuteSerializer(serializers.ModelSerializer):
    value = serializers.DateTimeField(format="%Y-%m-%dT%H:%M")
    is_booked = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()


    class Meta:
        model = Booking
        fields = ('value', 'is_available', 'is_booked')


    def get_is_available(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        value = booking['value']

        year = time_query_datetime.year
        month = time_query_datetime.month
        day = time_query_datetime.day
        hour = time_query_datetime.hour
        minute = value.minute

        current_datetime = datetime.datetime.now()
        current_year = current_datetime.year
        current_month = current_datetime.month
        current_day = current_datetime.day
        current_hour = current_datetime.hour
        current_minute = current_datetime.minute

        rental = self.context.get('rental')
        start_year = rental.rental_period.start_date.year
        end_year = rental.rental_period.end_date.year
        start_month = rental.rental_period.start_date.month
        end_month = rental.rental_period.end_date.month
        start_day = rental.rental_period.start_date.day
        end_day = rental.rental_period.end_date.day
        start_hour = rental.rental_period.start_time.hour
        end_hour = rental.rental_period.end_time.hour
        start_minute = rental.rental_period.start_time.minute
        end_minute = rental.rental_period.end_time.minute


        if year < current_year:
            return False
        elif year == current_year and month < current_month:
            return False
        elif year == current_year and month == current_month and day < current_day:
            return False
        elif year == current_year and month == current_month and day == current_day and hour < current_hour:
            return False
        elif (year < start_year or year > end_year or
                (year == start_year and month < start_month) or
                (year == end_year and month > end_month) or
                (year == start_year and month == start_month and day < start_day) or
                (year == end_year and month == end_month and day > end_day) or
                (year == start_year and month == start_month and day == start_day and hour < start_hour) or
                (year == end_year and month == end_month and day == end_day and hour > end_hour) or
                (
                        year == start_year and month == start_month and day == start_day and hour == start_hour and minute < start_minute) or
                (
                        year == end_year and month == end_month and day == end_day and hour == end_hour and minute > end_minute)):
            return False
        elif year == current_year and month == current_month and day == current_day and hour == current_hour and \
                minute < current_minute:
            return False

        return True

    def get_is_booked(self, booking):
        time_query = self.context.get('time_query')

        if not time_query:
            return False

        try:
            time_query_datetime = datetime.datetime.strptime(time_query, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False

        value = booking['value']
        current_date = time_query_datetime
        current_hour = time_query_datetime.hour
        minute = value.minute

        rental = self.context.get('rental')

        bookings = rental.user_bookings.filter(
            start_time__date=current_date,
            start_time__hour=current_hour,
            start_time__minute__lte=minute,
            end_time__date=current_date,
            end_time__hour=current_hour,
            end_time__minute__gte=minute,
            transaction__is_processed=True
        )
        return bookings.exists()


class BookingItemRentalRetrieveSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    videos = VideoSerializer(many=True)
    rental_period = RentItemsPeriodSerializer()
    ticket_period = TicketPeriodSerializer()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'price', 'discount', 'images', 'videos', 'rental_period', 'ticket_period'
        )

class TicketWithTicketPeriodSerializer(serializers.ModelSerializer):
    ticket_period = TicketPeriodSerializer()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'ticket_period'
        )


class TicketItemRetrieveSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    videos = VideoSerializer(many=True)
    ticket_period = TicketPeriodSerializer()
    subcategory = SubcategorySerializer()
    currency = serializers.CharField(source='organization.currency.code')

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'price', 'discount', 'images', 'videos', 'subcategory', 'currency',
                  'ticket_period'
        )

class BookInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = ('id', 'organization', 'start_time', 'end_time', )


class SubmitUserResumeRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ResumeRequest
        fields = ('id', 'sender_user', 'organization', 'item', 'show_contacts', 'phone_numbers',
                  'links', 'text')


class SubmitOrganizationResumeRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ResumeRequest
        fields = ('id', 'sender_organization', 'organization', 'item', 'show_contacts', 'phone_numbers',
                  'links', 'text')

class ResumeItemRetrieveSerializer(serializers.ModelSerializer):
    organization = ItemFeedOrganizationSerializer(allow_null=True)
    images = ImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'organization',
            'salary_from', 'salary_to', 'is_published', 'updated_at', 'images', 'currency'
        )


class UserResumeRequestSerializer(serializers.ModelSerializer):
    sender_user = ProfileSerializer(many=False, allow_null=True)
    organization = OrganizationTitleImageSerializer(allow_null=True)
    item = ResumeItemRetrieveSerializer(many=False, allow_null=True)
    processed_by = ProfileSerializer(many=False, allow_null=True)

    class Meta:
        model = ResumeRequest
        fields = ('id', 'sender_user', 'organization', 'processed_by', 'item', 'status')


class UserResumeRequestAcceptedSerializer(serializers.ModelSerializer):
    sender_user = ProfileSerializer(many=False, allow_null=True)
    organization = OrganizationTitleImageSerializer(allow_null=True)
    item = ResumeItemRetrieveSerializer(many=False, allow_null=True)
    processed_by = ProfileSerializer(many=False, allow_null=True)

    class Meta:
        model = ResumeRequest
        fields = ('id', 'sender_user', 'organization', 'processed_by', 'item', 'phone_numbers', 'links', 'status',
                  'text')


class OrganizationResumeRequestSerializer(serializers.ModelSerializer):
    sender_organization = OrganizationNotificationInfo(many=False, allow_null=True)
    organization = OrganizationTitleImageSerializer(allow_null=True)
    item = ResumeItemRetrieveSerializer(many=False, allow_null=True)
    processed_by = ProfileSerializer(many=False, allow_null=True)

    class Meta:
        model = ResumeRequest
        fields = ('id', 'sender_organization', 'organization', 'processed_by', 'item', 'status')


class OrganizationResumeRequestAcceptedSerializer(serializers.ModelSerializer):
    sender_organization = OrganizationNotificationInfo(many=False, allow_null=True)
    organization = OrganizationTitleImageSerializer(allow_null=True)
    item = ResumeItemRetrieveSerializer(many=False, allow_null=True)
    processed_by = ProfileSerializer(many=False, allow_null=True)

    class Meta:
        model = ResumeRequest
        fields = ('id', 'sender_organization', 'organization', 'processed_by', 'item', 'phone_numbers', 'links',
                  'status', 'text')


class AcceptDeclineUserResumeRequestSerializer(serializers.Serializer):
    resume_request_id = serializers.IntegerField(required=True)


class ResumeFilterQuaryParamsSerializer(serializers.Serializer):
    country = serializers.CharField(required=False)
    city = serializers.IntegerField(required=False)
    salary_from = serializers.IntegerField(required=False)
    salary_to = serializers.IntegerField(required=False)
    gender = serializers.CharField(required=False, allow_blank=True)
    has_work_experience = serializers.BooleanField(required=False, allow_null=True)
    has_education = serializers.BooleanField(required=False, allow_null=True)


class BookInfoWithClientSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Booking
        fields = ('id', 'organization', 'client', 'start_time', 'end_time',)


class BookInfoWithUTCSerializer(serializers.ModelSerializer):
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)

    class Meta:
        model = Booking
        fields = ('id', 'organization', 'start_time', 'end_time', 'utc_offset_minutes')


class TransactionBookingInfoSerializer(serializers.ModelSerializer):
    item = BookingItemRentalRetrieveSerializer()
    start_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M')
    end_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M')

    class Meta:
        model = Booking
        fields = ('id', 'organization', 'item', 'start_time', 'end_time', 'is_active')


class IsActiveBookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = ('id', 'is_active')


class IsActiveTicketSerializer(serializers.ModelSerializer):
    item = TicketItemRetrieveSerializer()
    activated_time = serializers.SerializerMethodField()

    def get_activated_time(self, ticket: Ticket):
        if ticket.is_active:
            return ticket.updated_at
        return None

    class Meta:
        model = Ticket
        fields = ('id', 'item', 'is_active', 'activated_time')

class RentalTicketListSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    videos = VideoSerializer(many=True)
    subcategory = ItemSubcategoryBriefSerializer()
    ticket_period = TicketPeriodSerializer()


    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang',
            'price', 'discount', 'instagram_link', 'is_published', 'is_hidden',
            'created_at', 'updated_at', 'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'is_updated', 'purchase_type', 'ticket_period'
        )
        read_only_fields = ['name_lang', 'description_lang']
