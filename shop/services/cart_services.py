from decimal import Decimal
from sqlite3 import IntegrityError
from typing import Tuple

from django.db import transaction
from django.db.models import F, Sum, DecimalField
from django.db.models.functions import Coalesce

from common.exceptions import ObjectNotFoundException, PermissionDeniedException, IntegrityException, \
    BadRequestException
from organizations.services.organization_services import OrganizationService
from shop.models import CartItem, Cart, ShopItem, DeliveryInfo
from transactions.models import Transaction
from transactions.services.transaction_services import TransactionService
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
            total = item.count + total
        return total

    @classmethod
    def checkout_cart(cls, user: User, cart_id: int):
        cart = cls.get(user=user, id=cart_id)
        cart.delete()
        # ToDo: Put cart contents to transaction

    @classmethod
    def close_the_cart(cls, user: User, cart_id: int):
        cart = cls.get(id=cart_id)
        if cart.user != user:
            raise PermissionDeniedException('No rights to change this cart')
        if not cart.transaction:
            try:
                cls.create_transaction(cart)
            except IntegrityError:
                raise IntegrityException('Could not add transaction')
        cart.is_open = False
        cart.save()
        return cart

    @classmethod
    def create_transaction(cls, cart: Cart):
        try:
            original_price, discounted_price = cls.get_total_prices_in_cart(cart)
            transaction = Transaction.objects.create(client=cart.user, organization=cart.organization, cart=cart,
                                                     type="online", original_amount=original_price,
                                                     currency=cart.organization.currency, status='in_progress',
                                                     savings=original_price - discounted_price)
            return transaction
        except IntegrityError:
            raise IntegrityException('Could not create transaction')

    @classmethod
    def can_user_change_cart(cls, user: User, cart: Cart) -> bool:
        return (cart.user == user and cart.is_open) or OrganizationService.user_can_sell(organization=cart.organization,
                                                                                         user=user)

    @classmethod
    def bulk_update(cls, cart: Cart, items, user: User):
        if not cls.can_user_change_cart(user=user, cart=cart):
            raise PermissionDeniedException('No rights to change this cart')
        CartItem.objects.filter(cart=cart).delete()
        if not cart.is_open:
            raise ObjectNotFoundException(message="Cart was closed")
        for data in items:
            if data['count']:
                CartItem.objects.create(cart=cart, item=data['item'], count=data['count'])
        if not CartItem.objects.filter(cart=cart):
            cart.delete()


class CartItemService:
    @classmethod
    @transaction.atomic
    def change_cart_item_count(cls, user: User, shop_item: ShopItem, change: int) -> int:
        cart, created = Cart.objects.get_or_create(user=user, organization=shop_item.organization, is_open=True)

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
    @transaction.atomic
    def delete_item_from_all_carts(cls, item: ShopItem):
        cart_items = CartItem.objects.filter(item=item)

        for cart_item in cart_items:
            cart = Cart.objects.get(items=cart_item)
            cart_item.delete()

            if cart.items.count() == 0:
                cart.delete()

    @classmethod
    def get_all_items_amount(cls, user: User) -> int:
        carts = Cart.objects.filter(user=user, is_open=True)
        cart_items = CartItem.objects.filter(cart__in=carts)
        total = 0
        for item in cart_items:
            total = item.count + total
        return total


class DeliveryInfoService:
    @classmethod
    def create(cls, *args, **kwargs):
        try:
            transaction = kwargs['transaction']
            transaction.delivery_type = 'cash_courier'
            transaction.save()
            return DeliveryInfo.objects.create(*args, **kwargs)
        except Exception as e:
            raise BadRequestException(f'Could not add delivery info , {e}')
