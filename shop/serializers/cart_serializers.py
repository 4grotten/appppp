from rest_framework import serializers

from common.models import File
from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import (
    OrganizationTitleImageSerializer, OrganizationTitleCurrencySerializer, OrganizationTitleImageCurrencySerializer
)
from shop.models import ShopItem, Cart, CartItem, DeliveryInfo
from shop.serializers.item_serializers import ItemInCartSerializer
from shop.services.cart_services import CartService


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemInCartSerializer()

    class Meta:
        model = CartItem
        fields = ('count', 'item',)


class CartSerializer(serializers.ModelSerializer):
    organization = OrganizationTitleCurrencySerializer()
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


class CartListSerializer(serializers.ModelSerializer):
    organization = OrganizationTitleImageCurrencySerializer()
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
        return ImageSerializer(images, many=True, context=self.context).data

    class Meta:
        model = Cart
        fields = ('id', 'items_count', 'totals', 'organization', 'images',)


class CartItemCountChangeSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())
    change = serializers.IntegerField()


class CartAllItemsCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class DeliveryInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryInfo
        fields = ('address', 'apartment', 'intercom', 'entrance', 'floor', 'phone', 'comment')
