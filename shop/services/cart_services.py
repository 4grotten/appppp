from decimal import Decimal
from sqlite3 import IntegrityError
from typing import Tuple

from django.db import transaction
from django.db.models import F, Sum, DecimalField
from django.db.models.functions import Coalesce

from common.exceptions import ObjectNotFoundException, PermissionDeniedException, IntegrityException, \
    BadRequestException
from notifications.constants import ACCEPT_DISCOUNT_TYPE, ACCEPT_ORDER_CLIENT_TYPE, PRODUCT_MODE, \
    REQUEST_ORDER_CLIENT_TYPE, REQUEST_ORDER_TYPE
from organizations.services.organization_services import OrganizationService
from shop.models import CartItem, Cart, ShopItem, DeliveryInfo
from transactions.models import Transaction
from transactions.services.transaction_services import TransactionService
from users.models import User
from notifications.tasks import sent_notification, send_notifications_organization_members


class CartService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Cart.objects.get(*args, **kwargs)
        except Cart.DoesNotExist:
            raise ObjectNotFoundException('Cart not found')

    @classmethod
    def get_related(cls, *args, **kwargs):
        try:
            return Cart.objects \
                .select_related('transaction', 'organization') \
                .get(*args, **kwargs)
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
        if not cart.is_open:
            raise BadRequestException('Cart is already closed')
        current_transaction = cls.create_transaction(cart)
        cart.is_open = False
        try:
            cart.save(update_fields=["is_open"])
        except IntegrityError:
            raise IntegrityException('Could not add transaction')
        finally:
            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                mode=PRODUCT_MODE,
                notification_type=REQUEST_ORDER_CLIENT_TYPE,
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id,
                                total_price=str(current_transaction.final_amount),
                                currency=current_transaction.currency.code)
            )
            send_notifications_organization_members.delay(
                members_organization_id=current_transaction.organization_id,
                mode=PRODUCT_MODE,
                sender_id=current_transaction.client_id,
                with_permissions=dict(can_see_stats=True),
                notification_type=REQUEST_ORDER_TYPE,
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id,
                                total_price=str(current_transaction.final_amount),
                                currency=current_transaction.currency.code)
            )
            return cart

    @classmethod
    def create_transaction(cls, cart: Cart):
        try:
            original_price, discounted_price = cls.get_total_prices_in_cart(cart)
            transaction = Transaction.objects.create(client=cart.user, organization=cart.organization, cart=cart,
                                                     type="online", original_amount=original_price,
                                                     currency=cart.organization.currency,
                                                     status=Transaction.IN_PROGRESS,
                                                     savings=original_price - discounted_price)
            return transaction
        except IntegrityError:
            raise IntegrityException('Could not create transaction')

    @classmethod
    def can_user_change_cart(cls, user: User, cart: Cart) -> bool:
        return (cart.user == user and cart.is_open) or OrganizationService.user_can_sell(organization=cart.organization,
                                                                                         user=user)

    @classmethod
    def can_user_change_closed_cart(cls, user: User, cart: Cart) -> bool:
        return OrganizationService.user_can_sell(organization=cart.organization,
                                                 user=user)

    @classmethod
    def bulk_update(cls, cart: Cart, items, user: User):

        if (not ((cls.can_user_change_cart(user=user, cart=cart) and cart.is_open) or cls.can_user_change_closed_cart(
                user=user, cart=cart)) or (cart.transaction and cart.transaction.status != Transaction.IN_PROGRESS)):
            raise PermissionDeniedException('No rights to change this cart')

        CartItem.objects.filter(cart=cart).delete()

        for data in items:
            if data['count'] and data['item'].organization == cart.organization:
                CartItem.objects.create(cart=cart, item=data['item'], count=data['count'])

        if cart.transaction and not cart.is_open:
            totals = cart.items.aggregate(
                original_price=Coalesce(Sum(F('count') * F('item__price'), output_field=DecimalField()), 0),
                discounted_price=Coalesce(Sum(F('count') * F('item__discounted_price'), output_field=DecimalField()), 0)
            )
            original_price = totals['original_price']
            discounted_price = totals['discounted_price']
            role = OrganizationService.get_user_role_in_organization(
                organization=cart.organization,
                user=user
            )
            try:
                cart.transaction.currency = cart.organization.currency
                cart.transaction.processed_by = user
                cart.transaction.employee_name = user.full_name
                cart.transaction.employee_role = role
                cart.transaction.employee_avatar = user.avatar
                cart.transaction.original_amount = original_price
                cart.transaction.savings = original_price - discounted_price
                cart.transaction.save(update_fields=[
                    "currency",
                    "processed_by",
                    "employee_name",
                    "employee_role",
                    "employee_avatar",
                    "original_amount",
                    "savings"
                ])
            except IntegrityError:
                raise IntegrityException('Could not complete transaction')

        return cart


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
