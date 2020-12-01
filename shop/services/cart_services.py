from decimal import Decimal
from typing import Tuple

from django.db import transaction
from django.db.models import F, Sum, DecimalField
from django.db.models.functions import Coalesce

from common.exceptions import ObjectNotFoundException
from shop.models import CartItem, Cart, ShopItem
from users.models import User


class CartService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Cart.objects.get(*args, **kwargs)
        except Cart.DoesNotExist:
            raise ObjectNotFoundException('Cart not found')

    @classmethod
    def get_total_prices_in_cart(cls, cart: Cart) -> Tuple[Decimal, Decimal]:
        totals = cart.items.aggregate(
            original_price=Coalesce(Sum(F('count') * F('item__price'), output_field=DecimalField()), 0),
            discounted_price=Coalesce(Sum(F('count') * F('item__discounted_price'), output_field=DecimalField()), 0)
        )

        return totals['original_price'], totals['discounted_price']

    @classmethod
    def get_total_items_in_cart(cls, cart: Cart) -> int:
        cart_items = CartItem.objects.filter(cart=cart)
        total = 0
        for item in cart_items:
            total = item.count+total
        return total

    @classmethod
    def checkout_cart(cls, user: User, cart_id: int):
        cart = cls.get(user=user, id=cart_id)
        cart.delete()
        # ToDo: Put cart contents to transaction


class CartItemService:
    @classmethod
    @transaction.atomic
    def change_cart_item_count(cls, user: User, shop_item: ShopItem, change: int) -> int:
        cart, created = Cart.objects.get_or_create(user=user, organization=shop_item.organization)

        if created:
            if change <= 0:
                return 0
            CartItem.objects.create(cart=cart, item=shop_item, count=change)
            return change

        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=shop_item)

        if cart_item.count + change <= 0:
            cart_item.delete()
            if cart.items.count() == 0:
                cart.delete()
            return 0
        else:
            cart_item.count = F('count') + change
            cart_item.save()
            cart_item.refresh_from_db()
            return cart_item.count

    @classmethod
    def get_all_items_amount(cls, user: User) -> int:
        carts = Cart.objects.filter(user=user)
        cart_items = CartItem.objects.filter(cart__in=carts)
        total = 0
        for item in cart_items:
            total = item.count + total
        return total
