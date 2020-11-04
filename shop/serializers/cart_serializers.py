from rest_framework import serializers

from common.models import File
from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import OrganizationTitleImageSerializer
from shop.models import ShopItem, Cart, CartItem
from shop.services.cart_services import CartService


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'


class CartListSerializer(serializers.ModelSerializer):
    organization = OrganizationTitleImageSerializer()
    # ToDo: ask if items_count unique or total?
    items_count = serializers.IntegerField()
    images = serializers.SerializerMethodField()
    totals = serializers.SerializerMethodField()

    def get_totals(self, cart: Cart) -> dict:
        original_price, discounted_price = CartService.get_total_prices_in_cart(cart=cart)

        return {
            'original_price': original_price,
            'discounted_price': discounted_price
        }

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
