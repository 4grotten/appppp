from rest_framework import serializers

from common.models import File
from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import OrganizationShortInfoWithCurrencySerializer
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, Cart, CartItem, DeliveryInfo
from shop.serializers.item_serializers import ItemInCartSerializer
from shop.services.cart_services import CartService


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemInCartSerializer()

    class Meta:
        model = CartItem
        fields = ('item', 'count',)


class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ('item', 'count',)


class CartSerializer(serializers.ModelSerializer):
    organization = OrganizationShortInfoWithCurrencySerializer()
    totals = serializers.SerializerMethodField()
    items = CartItemSerializer(many=True)

    def get_totals(self, cart: Cart) -> dict:
        original_price, discounted_price = CartService.get_total_prices_in_cart(cart=cart)

        return {
            'original_price': original_price,
            'discounted_price': discounted_price
        }

    class Meta:
        model = Cart
        fields = ('id', 'organization', 'totals', 'items',)


class EmployeeCartSerializer(CartSerializer):
    can_sell = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'can_sell', 'organization', 'totals', 'items',)

    def get_can_sell(self, cart: Cart) -> bool:
        return OrganizationService.user_can_sell(organization=cart.organization, user=cart.user)


class CartWithItemsSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ('id', 'items')


class CartUpdateSerializer(serializers.ModelSerializer):
    items = CartItemUpdateSerializer(many=True)

    class Meta:
        model = Cart
        fields = ('items',)


class CartListSerializer(serializers.ModelSerializer):
    organization = OrganizationShortInfoWithCurrencySerializer()
    items_count = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    totals = serializers.SerializerMethodField()

    def get_totals(self, cart: Cart) -> dict:
        original_price, discounted_price = CartService.get_total_prices_in_cart(cart=cart)

        return {
            'original_price': original_price,
            'discounted_price': discounted_price
        }

    def get_items_count(self, cart: Cart) -> int:
        items_count = CartService.get_total_items_in_cart(cart=cart)
        return items_count

    def get_images(self, cart: Cart) -> list:
        item_image_ids = cart.items.values_list('item__images', flat=True)
        images = File.objects.filter(id__in=item_image_ids, order=0)[:3]

        images_to_fill = 3 - images.count()
        images_list = ImageSerializer(images, many=True, context=self.context).data

        if images_to_fill > 0:
            cart_items_with_only_insta_video = cart.items.filter(item__images__isnull=True)[:images_to_fill]
            for cart_item in cart_items_with_only_insta_video:
                insta_data = cart_item.item.instagram_data.filter(thumbnail_url__isnull=False).first()
                if insta_data is not None:
                    item_video_thumbnail_url = insta_data.thumbnail_url
                    images_list.append({
                        "id": 0,
                        "file": item_video_thumbnail_url,
                        "name": "Cart thumbnail",
                        "large": item_video_thumbnail_url,
                        "medium": item_video_thumbnail_url,
                        "small": item_video_thumbnail_url
                    })
        return images_list

    class Meta:
        model = Cart
        fields = ('id', 'items_count', 'totals', 'organization', 'images',)


class CartItemCountChangeSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())
    change = serializers.IntegerField()


class BulkCartItemCountChangeSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())
    count = serializers.IntegerField()


class CartAllItemsCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class DeliveryInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryInfo
        fields = ('address', 'apartment', 'intercom', 'entrance', 'floor', 'phone', 'comment')
