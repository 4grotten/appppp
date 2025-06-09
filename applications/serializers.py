from rest_framework import serializers

from applications.models import UserApp, UserAppBanner, UserAppCategory, UserAppType, UserAppBalance, \
    UserAppTransaction, UserAppPurchase, PlatformCommission, AddedApp
from common.models import File
from common.serializers import ImageSerializer
from users.serializers import UserShortInfoSerializer


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

        if not obj.price:
            return True

        return obj.purchases.filter(user=user, is_paid=True).exists()

    class Meta:
        model = UserApp
        fields = (
            'id', 'title', 'title_lang', 'description', 'description_lang', 'types', 'image', 'selected_banner',
            'app_images', 'app_link', 'price', 'instagram_link', 'youtube_links', 'support_link', 'company_name',
            'terms_link', 'is_paid', 'is_hidden'
        )


class UserAppListSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    selected_banner = UserAppBannerSerializer()
    types = UserAppTypeSerializer(many=True)
    is_paid = serializers.SerializerMethodField()
    is_added = serializers.SerializerMethodField()
    is_my_app = serializers.SerializerMethodField()

    def get_is_paid(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            return False

        if not obj.price:
            return True

        return obj.purchases.filter(user=user, is_paid=True).exists()

    def get_is_added(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            return False

        return AddedApp.objects.filter(user=user, user_app=obj).exists()

    def get_is_my_app(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        return user.is_authenticated and obj.owner_id == user.id

    class Meta:
        model = UserApp
        fields = ('id', 'title', 'title_lang', 'types', 'image', 'selected_banner', 'is_paid', 'is_added', 'is_my_app',
                  'is_hidden')


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


class UserAppBalanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAppBalance
        fields = ("id", "total_earned", "current_balance", "currency")


class UserAppWithImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    selected_banner = UserAppBannerSerializer()
    types = UserAppTypeSerializer(many=True)

    class Meta:
        model = UserApp
        fields = ('id', 'title', 'image', 'selected_banner', 'types')


class UserAppPurchaseSerializer(serializers.ModelSerializer):
    app = UserAppWithImageSerializer()
    user = UserShortInfoSerializer()


    class Meta:
        model = UserAppPurchase
        fields = ("id", "app", "user", "is_paid", )


class UserAppPurchaseWithProfitSerializer(serializers.ModelSerializer):
    app = UserAppWithImageSerializer()
    user = UserShortInfoSerializer()
    profit_amount = serializers.SerializerMethodField()
    commission_percent = serializers.SerializerMethodField()
    original_amount = serializers.SerializerMethodField()

    def get_profit_amount(self, obj):
        transaction = obj.referral_transactions.first()
        return transaction.profit_amount if transaction else None

    def get_original_amount(self, obj):
        transaction = obj.referral_transactions.first()
        return transaction.original_amount if transaction else None

    def get_commission_percent(self, obj):
        commission = PlatformCommission.objects.first()
        return commission.commission_percent if commission else "20"

    class Meta:
        model = UserAppPurchase
        fields = (
            "id",
            "app",
            "user",
            "is_paid",
            "original_amount",
            "profit_amount",
            "commission_percent",
            "created_at",
        )


class UserAppPurchasesSerializer(serializers.ModelSerializer):
    app = UserAppWithImageSerializer()
    amount = serializers.DecimalField(source='transaction.original_amount', max_digits=10, decimal_places=2)

    class Meta:
        model = UserAppPurchase
        fields = (
            'id', 'created_at', 'app', 'amount'
        )


class UserAppChangeVisibilitySerializer(serializers.Serializer):
    is_hidden = serializers.BooleanField()
    app = serializers.PrimaryKeyRelatedField(queryset=UserApp.objects.all())