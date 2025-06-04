from rest_framework import serializers

from applications.models import UserApp, UserAppBanner, UserAppCategory, UserAppType
from common.models import File
from common.serializers import ImageSerializer


class UserAppCreateSerializer(serializers.ModelSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all()
    )
    types = serializers.PrimaryKeyRelatedField(
        queryset=UserAppType.objects.all(), many=True, required=True
    )
    banners_image_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=File.objects.all()),
        required=True
    )
    selected_banner_file_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), required=True
    )
    description = serializers.CharField(required=True)

    class Meta:
        model = UserApp
        fields = (
            'title', 'description', 'types', 'image_id', 'banners_image_ids', 'selected_banner_file_id', 'app_images',
            'app_link', 'price', 'instagram_link', 'youtube_links', 'support_link', 'company_name', 'terms_link'
        )

    def validate(self, attrs):
        attrs['owner'] = self.context['request'].user
        return attrs


class UserAppBannerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = UserAppBanner
        fields = ('id', 'image', 'is_default')


class UserAppTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAppType
        fields = ('id', 'title',)


class UserAppCategorySerializer(serializers.ModelSerializer):
    types = UserAppTypeSerializer(many=True)

    class Meta:
        model = UserAppCategory
        fields = ('id', 'name', 'types')


class UserAppDetailedSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    app_images = ImageSerializer(many=True)
    selected_banner = UserAppBannerSerializer()
    types = UserAppTypeSerializer(many=True)
    is_paid = serializers.SerializerMethodField()

    def get_is_paid(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            return False

        if obj.owner == user:
            return True

        if not obj.price:
            return True

        return obj.purchases.filter(user=user, is_paid=True).exists()

    class Meta:
        model = UserApp
        fields = (
            'id', 'title', 'title_lang', 'description', 'description_lang', 'types', 'image', 'selected_banner',
            'app_images', 'app_link', 'price', 'instagram_link', 'youtube_links', 'support_link', 'company_name',
            'terms_link', 'is_paid'
        )


class UserAppListSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    selected_banner = UserAppBannerSerializer()
    types = UserAppTypeSerializer(many=True)
    is_paid = serializers.SerializerMethodField()

    def get_is_paid(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            return False

        if obj.owner == user:
            return True

        if not obj.price:
            return True

        return obj.purchases.filter(user=user, is_paid=True).exists()

    class Meta:
        model = UserApp
        fields = ('id', 'title', 'title_lang', 'types', 'image', 'selected_banner', 'is_paid')


class UserAppUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField()
    selected_banner_id = serializers.IntegerField(required=False)

    class Meta:
        model = UserApp
        fields = ('title', 'image_id', 'description', 'types', 'selected_banner_id', 'app_images',
                  'app_link', 'price', 'instagram_link', 'youtube_links', 'support_link', 'company_name', 'terms_link')


class UserAppBannerCreateSerializer(serializers.ModelSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), source='image', write_only=True
    )

    class Meta:
        model = UserAppBanner
        fields = ('image_id', )

    def create(self, validated_data):
        return UserAppBanner.objects.create(image=validated_data['image'])


class PurchaseUserAppSerializer(serializers.Serializer):
    app = serializers.PrimaryKeyRelatedField(queryset=UserApp.objects.all())
    utc_offset_minutes = serializers.IntegerField()
