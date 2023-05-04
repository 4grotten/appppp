import logging
from datetime import timedelta
from decimal import Decimal
from typing import Union

from django.db import IntegrityError, transaction
from django.db.models import Sum, OuterRef, Subquery, F, QuerySet, Q, DecimalField, Case, When, IntegerField, Max, \
    Count, Value
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from common.exceptions import (
    NotAcceptableException, ObjectNotFoundException, IntegrityException, PermissionDeniedException, BadRequestException,
    StockException,
)
from notifications.constants import (
    NOTIFICATION_MODE_DISCOUNT, DISCOUNT_COMPLETE_DESCRIPTION, WITHDRAW_CASHBACK_CLIENT_TITLE,
    CHARGE_CASHBACK_CLIENT_TITLE, CHARGE_CASHBACK_CLIENT, CHARGE_CASHBACK_SELLER, CHARGE_CASHBACK_SELLER_TITLE,
    WITHDRAW_CASHBACK_CLIENT, WITHDRAW_CASHBACK_SELLER_TITLE, WITHDRAW_CASHBACK_SELLER, REQUEST_ORDER_CLIENT_TYPE,
    NOTIFICATION_MODE_PRODUCT, ACCEPT_ORDER_CLIENT_TYPE, ACCEPT_ORDER_TYPE, DECLINE_ORDER_CLIENT_TYPE,
    DECLINE_ORDER_TYPE,
    REQUEST_ORDER_TYPE, NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION, NOTIFICATION_MODE_SYSTEM,
    NOTIFICATION_MODE_RENTAL, ACCEPT_RENTAL_CLIENT_TYPE, ACCEPT_RENTAL_TYPE, REQUEST_RENTAL_TYPE,
    REQUEST_RENTAL_CLIENT_TYPE, DECLINE_RENTAL_TYPE, DECLINE_RENTAL_CLIENT_TYPE, DECLINE_RENTAL_PAYMENT_TYPE,
    ACCEPT_RENTAL_PAYMENT_TYPE, ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE, DECLINE_RENTAL_PAYMENT_CLIENT_TYPE,
    DECLINE_ACCEPTED_RENTAL_TYPE, DECLINE_ACCEPTED_RENTAL_CLIENT_TYPE, ACTIVATE_RENTAL_CLIENT_TYPE
)
from notifications.models import Notification
from notifications.tasks import sent_notification, send_delivery_notitication_to_organization_or_client
from organizations.models import Organization, DiscountCard, Subscription, Membership
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.cumulative_group_services import CumulativeGroupService
from organizations.services.membership_services import MembershipService
from organizations.services.organization_services import OrganizationService
from shop.models import Cart, ShopItem, Booking
from shop.services.cart_services import CartService
from shop.services.booking_services import BookingService
from stock.models import ShopItemSizeCount
from transactions.models import Transaction
from transactions.services.stats_services import StatisticsService
from users.models import User
from users.services import UserService


class TransactionService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Transaction.objects.get(**kwargs)
        except Transaction.DoesNotExist:
            raise ObjectNotFoundException(_('Transaction not found'))

    @classmethod
    @transaction.atomic
    def preprocess_transaction(cls, client: User, organization: Organization, cart: Union[Cart, None],
                               processed_by: User) -> Transaction:
        if not OrganizationService.user_can_sell(organization=organization, user=processed_by):
            raise NotAcceptableException(_('No rights to sell in this organization'))

        if cart is not None and not cart.user == processed_by:
            raise NotAcceptableException(_('No rights to use this cart'))

        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)

        instance = Transaction.objects.create(client=client, organization=organization, processed_by=processed_by,
                                              employee_name=processed_by.full_name, employee_role=role,
                                              employee_avatar=processed_by.avatar, currency=organization.currency)

        if cart is not None:
            cart.transaction = instance
            cart.save()

        return instance

    @classmethod
    @transaction.atomic
    def preprocess_booking_transaction(cls, client: User, organization: Organization, booking: Booking,
                               processed_by: User) -> Transaction:
        if not OrganizationService.user_can_sell(organization=organization, user=processed_by):
            raise NotAcceptableException(_('No rights to book in this organization'))

        if booking is not None and not booking.user == processed_by:
            raise NotAcceptableException(_('No rights to use this booking'))

        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)

        instance = Transaction.objects.create(client=client, organization=organization, processed_by=processed_by,
                                              employee_name=processed_by.full_name, employee_role=role,
                                              employee_avatar=processed_by.avatar, currency=organization.currency)
        if booking is not None:
            booking.transaction = instance
            booking.save()

        return instance

    @classmethod
    def get_transaction(cls, transaction_id: int, requested_by: User) -> Transaction:
        instance = cls.get(id=transaction_id)

        # if instance.client != requested_by and not OrganizationService.user_can_see_stats(
        #         organization=instance.organization, user=requested_by):
        #     raise PermissionDeniedException(_('Permission denied'))

        return instance

    @classmethod
    @transaction.atomic
    def complete_transaction(cls, transaction_id: int, processed_by: User, original_amount: Decimal,
                             discount_percent: int, source_card: Union[DiscountCard, None], from_cashback: Decimal,
                             utc_offset_minutes: int, cart: Union[Cart, None] = None,
                             ) -> Transaction:

        current_transaction = cls.get(id=transaction_id, processed_by=processed_by, is_processed=False, type='offline',
                                      status=Transaction.IN_PROGRESS)
        organization = current_transaction.organization

        if source_card is not None and not OrganizationClientFinancialStatusService.can_use_given_card(
                client=current_transaction.client, card=source_card):
            raise NotAcceptableException(_('Client cannot use this card'))

        cashback_percent = 0
        if source_card is not None and source_card.type == DiscountCard.CASHBACK:
            cashback_percent = discount_percent
            discount_percent = 0

        if from_cashback > 0 and not OrganizationClientFinancialStatusService.has_enough_cashback_amount(
                client=current_transaction.client, organization=organization, amount=from_cashback):
            raise NotAcceptableException(_('Not enough accrued cashback amount'))

        transaction_cart = getattr(current_transaction, 'cart', None)
        if not transaction_cart == cart:
            raise NotAcceptableException(_('Transaction and cart do not match'))

        total_savings = (original_amount * discount_percent) / 100

        if cart is not None:
            items_price, discounted_items = CartService.get_total_prices_in_cart(cart=cart)
            if not original_amount == discounted_items:
                raise NotAcceptableException(_('Original amount do not match with cart amounts'))
            cart.is_open = False
            cart.save()
            original_amount = items_price
            total_savings = total_savings + (items_price - discounted_items)

        amount_to_pay = original_amount - total_savings
        if amount_to_pay < from_cashback:
            raise NotAcceptableException(_('Cashback amount is greater than original amount'))

        try:
            current_transaction.original_amount = original_amount
            current_transaction.savings = total_savings
            current_transaction.discount_percent = max(discount_percent, cashback_percent)
            current_transaction.from_cashback = from_cashback
            current_transaction.source_card = source_card
            current_transaction.is_processed = True
            current_transaction.status = Transaction.ACCEPTED
            current_transaction.delivery_type = Transaction.CART_CHECKOUT
            current_transaction.purchase_id = organization.running_purchase_id
            current_transaction.display_time = now() + timedelta(minutes=utc_offset_minutes)

            OrganizationService.increment_running_purchase_id(organization=organization)

            if source_card is not None:
                current_transaction.discount_type = source_card.type
            current_transaction.save()

            if source_card is None or source_card.type != DiscountCard.CASHBACK:
                sent_notification.delay(
                    recipient_id=current_transaction.client_id,
                    sender_id=current_transaction.processed_by_id,
                    mode=NOTIFICATION_MODE_PRODUCT,
                    notification_type=ACCEPT_ORDER_CLIENT_TYPE,
                    organization_id=current_transaction.organization_id,
                    extra_data=dict(transaction_id=current_transaction.id,
                                    total_price=current_transaction.final_amount,
                                    discount_percent=discount_percent,
                                    currency=current_transaction.currency.code)
                )
                sent_notification.delay(
                    recipient_id=current_transaction.processed_by_id,
                    sender_id=current_transaction.client_id,
                    mode=NOTIFICATION_MODE_PRODUCT,
                    notification_type=ACCEPT_ORDER_TYPE,
                    organization_id=current_transaction.organization_id,
                    extra_data=dict(transaction_id=current_transaction.id,
                                    total_price=current_transaction.final_amount,
                                    discount_percent=discount_percent,
                                    currency=current_transaction.currency.code)
                )

        except IntegrityError:
            raise IntegrityException(_('Could not complete transaction'))

        client_status = OrganizationClientFinancialStatusService.get_or_create(
            user=current_transaction.client,
            organization=organization
        )
        OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)

        if from_cashback > 0:
            to_subtract = min(client_status.accrued_cashback, from_cashback)

            client_status.accrued_cashback = F('accrued_cashback') - to_subtract
            client_status.save(update_fields=('accrued_cashback',))
            client_status.refresh_from_db()

            if to_subtract < from_cashback:
                remaining_amount = from_cashback - to_subtract
                OrganizationClientFinancialStatusService.use_corporate_cashback(
                    client=current_transaction.client, organization=organization,
                    amount=remaining_amount
                )

            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                sender_id=current_transaction.processed_by_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=WITHDRAW_CASHBACK_CLIENT,
                title=WITHDRAW_CASHBACK_CLIENT_TITLE.format(amount=str(from_cashback),
                                                            currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(from_cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )
            sent_notification.delay(
                recipient_id=current_transaction.processed_by_id,
                sender_id=current_transaction.client_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=WITHDRAW_CASHBACK_SELLER,
                title=WITHDRAW_CASHBACK_SELLER_TITLE.format(amount=str(from_cashback),
                                                            currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(from_cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )

        if source_card is not None and source_card.type == DiscountCard.CASHBACK:
            cashback = current_transaction.final_amount * cashback_percent / 100
            client_status.accrued_cashback = F('accrued_cashback') + cashback
            client_status.save(update_fields=('accrued_cashback',))
            client_status.refresh_from_db()

            current_transaction.to_cashback = cashback
            current_transaction.save(update_fields=('to_cashback',))

            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                sender_id=current_transaction.processed_by_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=CHARGE_CASHBACK_CLIENT,
                title=CHARGE_CASHBACK_CLIENT_TITLE.format(amount=str(cashback),
                                                          currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )
            sent_notification.delay(
                recipient_id=current_transaction.processed_by_id,
                sender_id=current_transaction.client_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=CHARGE_CASHBACK_SELLER,
                title=CHARGE_CASHBACK_SELLER_TITLE.format(amount=str(cashback),
                                                          currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )

        return current_transaction

    @classmethod
    @transaction.atomic
    def complete_booking_transaction(cls, transaction_id: int, processed_by: User, original_amount: Decimal,
                             discount_percent: int, source_card: Union[DiscountCard, None], from_cashback: Decimal,
                             booking: Booking) -> Transaction:

        current_transaction = cls.get(id=transaction_id, processed_by=processed_by, is_processed=False, type='offline',
                                      status=Transaction.IN_PROGRESS)
        organization = current_transaction.organization

        if source_card is not None and not OrganizationClientFinancialStatusService.can_use_given_card(
                client=current_transaction.client, card=source_card):
            raise NotAcceptableException(_('Client cannot use this card'))

        cashback_percent = 0
        if source_card is not None and source_card.type == DiscountCard.CASHBACK:
            cashback_percent = discount_percent
            discount_percent = 0

        if from_cashback > 0 and not OrganizationClientFinancialStatusService.has_enough_cashback_amount(
                client=current_transaction.client, organization=organization, amount=from_cashback):
            raise NotAcceptableException(_('Not enough accrued cashback amount'))

        transaction_cart = getattr(current_transaction, 'booking', None)
        if not transaction_cart == booking:
            raise NotAcceptableException(_('Transaction and booking do not match'))

        total_savings = (original_amount * discount_percent) / 100

        if booking is not None:
            items_price, discounted_items = BookingService.get_total_prices_in_booking(booking=booking)
            if not original_amount == discounted_items:
                raise NotAcceptableException(_('Original amount do not match with cart amounts'))
            booking.is_open = False
            booking.save()
            original_amount = items_price
            total_savings = total_savings + (items_price - discounted_items)

        amount_to_pay = original_amount - total_savings
        if amount_to_pay < from_cashback:
            raise NotAcceptableException(_('Cashback amount is greater than original amount'))

        try:
            current_transaction.original_amount = original_amount
            current_transaction.savings = total_savings
            current_transaction.discount_percent = max(discount_percent, cashback_percent)
            current_transaction.from_cashback = from_cashback
            current_transaction.source_card = source_card
            current_transaction.is_processed = True
            current_transaction.status = Transaction.ACCEPTED
            current_transaction.payment_status = Transaction.ACCEPTED
            current_transaction.delivery_type = Transaction.CART_CHECKOUT
            current_transaction.purchase_id = organization.running_purchase_id

            OrganizationService.increment_running_purchase_id(organization=organization)

            if source_card is not None:
                current_transaction.discount_type = source_card.type
            current_transaction.save()

            if source_card is None or source_card.type != DiscountCard.CASHBACK:
                sent_notification.delay(
                    recipient_id=current_transaction.client_id,
                    sender_id=current_transaction.processed_by_id,
                    mode=NOTIFICATION_MODE_RENTAL,
                    notification_type=ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE,
                    organization_id=current_transaction.organization_id,
                    extra_data=dict(transaction_id=current_transaction.id,
                                    total_price=current_transaction.final_amount,
                                    discount_percent=discount_percent,
                                    currency=current_transaction.currency.code)
                )
                sent_notification.delay(
                    recipient_id=current_transaction.processed_by_id,
                    sender_id=current_transaction.client_id,
                    mode=NOTIFICATION_MODE_RENTAL,
                    notification_type=ACCEPT_RENTAL_PAYMENT_TYPE,
                    organization_id=current_transaction.organization_id,
                    extra_data=dict(transaction_id=current_transaction.id,
                                    total_price=current_transaction.final_amount,
                                    discount_percent=discount_percent,
                                    currency=current_transaction.currency.code)
                )

        except IntegrityError:
            raise IntegrityException(_('Could not complete transaction'))

        client_status = OrganizationClientFinancialStatusService.get_or_create(
            user=current_transaction.client,
            organization=organization
        )
        OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)

        if from_cashback > 0:
            to_subtract = min(client_status.accrued_cashback, from_cashback)

            client_status.accrued_cashback = F('accrued_cashback') - to_subtract
            client_status.save(update_fields=('accrued_cashback',))
            client_status.refresh_from_db()

            if to_subtract < from_cashback:
                remaining_amount = from_cashback - to_subtract
                OrganizationClientFinancialStatusService.use_corporate_cashback(
                    client=current_transaction.client, organization=organization,
                    amount=remaining_amount
                )

            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                sender_id=current_transaction.processed_by_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=WITHDRAW_CASHBACK_CLIENT,
                title=WITHDRAW_CASHBACK_CLIENT_TITLE.format(amount=str(from_cashback),
                                                            currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(from_cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )
            sent_notification.delay(
                recipient_id=current_transaction.processed_by_id,
                sender_id=current_transaction.client_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=WITHDRAW_CASHBACK_SELLER,
                title=WITHDRAW_CASHBACK_SELLER_TITLE.format(amount=str(from_cashback),
                                                            currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(from_cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )

        if source_card is not None and source_card.type == DiscountCard.CASHBACK:
            cashback = current_transaction.final_amount * cashback_percent / 100
            client_status.accrued_cashback = F('accrued_cashback') + cashback
            client_status.save(update_fields=('accrued_cashback',))
            client_status.refresh_from_db()

            current_transaction.to_cashback = cashback
            current_transaction.save(update_fields=('to_cashback',))

            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                sender_id=current_transaction.processed_by_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=CHARGE_CASHBACK_CLIENT,
                title=CHARGE_CASHBACK_CLIENT_TITLE.format(amount=str(cashback),
                                                          currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )
            sent_notification.delay(
                recipient_id=current_transaction.processed_by_id,
                sender_id=current_transaction.client_id,
                mode=NOTIFICATION_MODE_DISCOUNT,
                notification_type=CHARGE_CASHBACK_SELLER,
                title=CHARGE_CASHBACK_SELLER_TITLE.format(amount=str(cashback),
                                                          currency=current_transaction.currency.code),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id, amount=str(cashback),
                                currency=current_transaction.currency.code,
                                final_amount=str(current_transaction.final_amount))
            )

        return current_transaction

    @classmethod
    def change_count_service(cls, cart_item, size):
        try:
            if ShopItemSizeCount.objects.filter(size=size, main_shop_item=cart_item.item).exists():
                item_size_count = ShopItemSizeCount.objects.filter(size=size, main_shop_item=cart_item.item)[0]
                try:
                    item_size_count.count -= cart_item.count
                    item_size_count.save()
                except IntegrityError:
                    raise StockException(_('Insufficient quantity in stock'))
        except IntegrityError:
            raise StockException(_('The product has no quantity'))

    @classmethod
    @transaction.atomic
    def complete_online_transaction(cls, request, transaction_id: int, utc_offset_minutes: int,
                                    processed_by: User) -> Transaction:
        current_transaction = cls.get(id=transaction_id, is_processed=False, type=Transaction.ONLINE,
                                      status=Transaction.IN_PROGRESS)
        organization = current_transaction.organization
        if not OrganizationService.user_can_sell(organization=organization, user=processed_by):
            raise NotAcceptableException(_('No rights to sell in this organization'))

        totals = current_transaction.cart.items.aggregate(
            original_price=Coalesce(Sum(F('count') * F('item__price'), output_field=DecimalField()), 0),
            discounted_price=Coalesce(Sum(F('count') * F('item__discounted_price'), output_field=DecimalField()), 0)
        )
        for cart_item in current_transaction.cart.items.all():
            if cart_item.size is not None and cart_item.size in cart_item.item.available_sizes.all():
                cls.change_count_service(size=cart_item.size, cart_item=cart_item)
            else:
                cls.change_count_service(size=None, cart_item=cart_item)

        original_price = totals['original_price']
        discounted_price = totals['discounted_price']
        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)
        from shop.serializers.cart_serializers import CartSerializer
        try:
            current_transaction.is_processed = True
            current_transaction.fixed_cart = CartSerializer(current_transaction.cart, context={
                'request': request}).data if current_transaction.cart else None
            current_transaction.processed_by = processed_by
            current_transaction.employee_role = role
            current_transaction.employee_name = processed_by.full_name
            current_transaction.employee_avatar = processed_by.avatar
            current_transaction.status = Transaction.ACCEPTED
            current_transaction.original_amount = original_price
            current_transaction.savings = original_price - discounted_price
            current_transaction.purchase_id = organization.running_purchase_id
            current_transaction.display_time = now() + timedelta(minutes=utc_offset_minutes)

            current_transaction.save()

            OrganizationService.increment_running_purchase_id(organization=organization)
        except IntegrityError:
            raise IntegrityException(_('Could not complete transaction'))
        client_status = OrganizationClientFinancialStatusService.get_or_create(
            user=current_transaction.client,
            organization=current_transaction.organization
        )
        OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)
        Notification.objects.filter(
            Q(extra_data__transaction_id=current_transaction.id) & (
                    Q(type=REQUEST_ORDER_TYPE) | Q(type=REQUEST_ORDER_CLIENT_TYPE))).delete()
        sent_notification.delay(
            recipient_id=current_transaction.client_id,
            sender_id=current_transaction.processed_by_id,
            mode=NOTIFICATION_MODE_PRODUCT,
            notification_type=ACCEPT_ORDER_CLIENT_TYPE,
            organization_id=current_transaction.organization_id,
            extra_data=dict(transaction_id=current_transaction.id,
                            total_price=current_transaction.final_amount,
                            discount_percent=0,
                            currency=current_transaction.currency.code)
        )
        sent_notification.delay(
            recipient_id=current_transaction.processed_by_id,
            sender_id=current_transaction.client_id,
            mode=NOTIFICATION_MODE_PRODUCT,
            notification_type=ACCEPT_ORDER_TYPE,
            organization_id=current_transaction.organization_id,
            extra_data=dict(transaction_id=current_transaction.id,
                            total_price=current_transaction.final_amount,
                            discount_percent=0,
                            currency=current_transaction.currency.code)
        )
        org = Organization.objects.exclude(Q(is_banned=True) | Q(is_deleted=True)).filter(
            is_delivery_service=True, country=organization.country).exists()
        if org:
            try:
                send_delivery_notitication_to_organization_or_client(current_transaction.cart.organization.owner,
                                                                     current_transaction.cart.id,
                                                                     NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                                                                     mode=NOTIFICATION_MODE_SYSTEM)

                organization_members = list(current_transaction.cart.organization.memberships.filter(
                    Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
                for member in organization_members:
                    send_delivery_notitication_to_organization_or_client(member.user,
                                                                         current_transaction.cart.id,
                                                                         NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                                                                         mode=NOTIFICATION_MODE_SYSTEM)
            except Exception as e:
                logging.exception(e)
        return current_transaction

    @classmethod
    @transaction.atomic
    def complete_booking_online_transaction(cls, request, transaction_id: int, utc_offset_minutes: int,
                                    processed_by: User) -> Transaction:
        current_transaction = cls.get(id=transaction_id, is_processed=False, type=Transaction.ONLINE,
                                      status=Transaction.IN_PROGRESS)
        organization = current_transaction.organization
        if not OrganizationService.user_can_sell(organization=organization, user=processed_by):
            raise NotAcceptableException(_('Permission denied'))
        item = ShopItem.objects.filter(id=current_transaction.booking.item.id)
        start_time = current_transaction.booking.start_time
        end_time = current_transaction.booking.end_time
        rent_time_type = item.values_list('rental_period__rent_time_type', flat=True).first()
        totals = dict()
        if rent_time_type == 'year':
            time_period = (int(end_time.year) - int(start_time.year)) + 1
            totals = item.aggregate(
                original_price=Coalesce(Sum(time_period * F('price'), output_field=DecimalField()), 0),
                discounted_price=Coalesce(Sum(time_period * F('discounted_price'), output_field=DecimalField()), 0)
            )
        if rent_time_type == 'month':
            time_period = (int(end_time.month) - int(start_time.month)) + 1
            totals = item.aggregate(
                original_price=Coalesce(Sum(time_period * F('price'), output_field=DecimalField()), 0),
                discounted_price=Coalesce(Sum(time_period * F('discounted_price'), output_field=DecimalField()), 0)
            )
        if rent_time_type == 'day':
            time_period = (int(end_time.day) - int(start_time.day)) + 1
            totals = item.aggregate(
                original_price=Coalesce(Sum(time_period * F('price'), output_field=DecimalField()), 0),
                discounted_price=Coalesce(Sum(time_period * F('discounted_price'), output_field=DecimalField()), 0)
            )
        if rent_time_type == 'hour':
            time_period = (int(end_time.hour) - int(start_time.hour)) + 1
            totals = item.aggregate(
                original_price=Coalesce(Sum(time_period * F('price'), output_field=DecimalField()), 0),
                discounted_price=Coalesce(Sum(time_period * F('discounted_price'), output_field=DecimalField()), 0)
            )
        if rent_time_type == 'minute':
            time_period = (int(end_time.minute) - int(start_time.minute)) + 1
            totals = item.aggregate(
                original_price=Coalesce(Sum(time_period * F('price'), output_field=DecimalField()), 0),
                discounted_price=Coalesce(Sum(time_period * F('discounted_price'), output_field=DecimalField()), 0)
            )

        # for cart_item in current_transaction.cart.items.all():
        #     if cart_item.size is not None and cart_item.size in cart_item.item.available_sizes.all():
        #         cls.change_count_service(size=cart_item.size, cart_item=cart_item)
        #     else:
        #         cls.change_count_service(size=None, cart_item=cart_item)

        original_price = totals['original_price']
        discounted_price = totals['discounted_price']
        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)
        from shop.serializers.cart_serializers import BookingSerializer
        try:
            current_transaction.fixed_cart = BookingSerializer(current_transaction.booking, context={
                'request': request}).data if current_transaction.booking else None

            current_transaction.processed_by = processed_by
            current_transaction.employee_role = role
            current_transaction.employee_name = processed_by.full_name
            current_transaction.employee_avatar = processed_by.avatar
            current_transaction.status = Transaction.ACCEPTED
            current_transaction.original_amount = original_price
            current_transaction.savings = original_price - discounted_price
            current_transaction.purchase_id = organization.running_purchase_id
            current_transaction.display_time = now() + timedelta(minutes=utc_offset_minutes)

            current_transaction.save()

            OrganizationService.increment_running_purchase_id(organization=organization)
        except IntegrityError:
            raise IntegrityException(_('Could not complete transaction'))
        client_status = OrganizationClientFinancialStatusService.get_or_create(
            user=current_transaction.client,
            organization=current_transaction.organization
        )
        OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)
        Notification.objects.filter(
            Q(extra_data__transaction_id=current_transaction.id) & (
                    Q(type=REQUEST_RENTAL_TYPE) | Q(type=REQUEST_RENTAL_CLIENT_TYPE))).delete()
        sent_notification.delay(
            recipient_id=current_transaction.client_id,
            sender_id=current_transaction.processed_by_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=ACCEPT_RENTAL_CLIENT_TYPE,
            organization_id=current_transaction.organization_id,
            extra_data=dict(transaction_id=current_transaction.id,
                            total_price=current_transaction.final_amount,
                            discount_percent=0,
                            currency=current_transaction.currency.code)
        )
        sent_notification.delay(
            recipient_id=current_transaction.processed_by_id,
            sender_id=current_transaction.client_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=ACCEPT_RENTAL_TYPE,
            organization_id=current_transaction.organization_id,
            extra_data=dict(transaction_id=current_transaction.id,
                            total_price=current_transaction.final_amount,
                            discount_percent=0,
                            currency=current_transaction.currency.code)
        )
        org = Organization.objects.exclude(Q(is_banned=True) | Q(is_deleted=True)).filter(
            is_delivery_service=True, country=organization.country).exists()
        if org:
            try:
                send_delivery_notitication_to_organization_or_client(current_transaction.booking.organization.owner,
                                                                     current_transaction.booking.id,
                                                                     NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                                                                     mode=NOTIFICATION_MODE_SYSTEM)

                organization_members = list(current_transaction.cart.organization.memberships.filter(
                    Q(role__can_edit_organization=True) | Q(role__can_see_stats=True) | Q(role__can_deliver=True)))
                for member in organization_members:
                    send_delivery_notitication_to_organization_or_client(member.user,
                                                                         current_transaction.cart.id,
                                                                         NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                                                                         mode=NOTIFICATION_MODE_SYSTEM)
            except Exception as e:
                logging.exception(e)
        return current_transaction

    @classmethod
    @transaction.atomic
    def create_offline_transaction_from_cart(cls, request, cart: Cart, utc_offset_minutes: int) -> Transaction:
        organization = cart.organization
        processed_by = cart.user
        client = UserService.get_common_user()
        original_price, discounted_price = CartService.get_total_prices_in_cart(cart)
        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)
        from shop.serializers.cart_serializers import CartSerializer

        fixed_cart = CartSerializer(cart, context={'request': request}).data
        offline_transaction = Transaction.objects.create(
            cart=cart,
            client=client,
            organization=organization,
            type='offline',
            original_amount=original_price,
            currency=organization.currency,
            status=Transaction.ACCEPTED,
            savings=original_price - discounted_price,
            is_processed=True,
            processed_by=processed_by,
            employee_name=processed_by.full_name,
            employee_avatar=processed_by.avatar,
            employee_role=role,
            delivery_type=Transaction.CART_CHECKOUT,
            fixed_cart=fixed_cart,
            purchase_id=organization.running_purchase_id,
            display_time=now() + timedelta(minutes=utc_offset_minutes),
        )

        for cart_item in offline_transaction.cart.items.all():
            if cart_item.size is not None and cart_item.size in cart_item.item.available_sizes.all():
                cls.change_count_service(size=cart_item.size, cart_item=cart_item)
            else:
                cls.change_count_service(size=None, cart_item=cart_item)

        OrganizationService.increment_running_purchase_id(organization=organization)

        return offline_transaction

    @classmethod
    @transaction.atomic
    def create_offline_transaction_from_booking(cls, request, booking: Booking, utc_offset_minutes: int) -> Transaction:
        organization = booking.organization
        processed_by = booking.user
        client = UserService.get_common_user()
        original_price, discounted_price = BookingService.get_total_prices_in_booking(booking=booking)
        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)
        from shop.serializers.cart_serializers import BookingSerializer

        fixed_cart = BookingSerializer(booking, context={'request': request}).data
        with transaction.atomic():
            offline_transaction, _ = Transaction.objects.get_or_create(
                booking=booking,
                client=booking.user,
                defaults={
                    "organization": organization,
                    "type": Transaction.OFFLINE,
                    "original_amount": original_price,
                    "currency": organization.currency,
                    "status": Transaction.ACCEPTED,
                    "savings": original_price - discounted_price,
                    "is_processed": True,
                    "payment_status":Transaction.ACCEPTED,
                    "processed_by": processed_by,
                    "employee_name": processed_by.full_name,
                    "employee_avatar": processed_by.avatar,
                    "employee_role": role,
                    "fixed_cart": fixed_cart,
                    "purchase_id": organization.running_purchase_id,
                    "display_time": now() + timedelta(minutes=utc_offset_minutes)
                }
            )

        OrganizationService.increment_running_purchase_id(organization=organization)

        return offline_transaction

    @classmethod
    def get_user_transaction_organizations(cls, client: User, start_date, end_date):
        transactions = Transaction.objects.filter(client=client, is_processed=True)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(created_at__range=[start_date, end_date])

        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).annotate(
            latest_transaction_time=Subquery(
                Transaction.objects.filter(organization=OuterRef('pk'), client=client,
                                           ).order_by('-updated_at').values('updated_at')[:1]
            )
        ).order_by('-latest_transaction_time')
        return organizations

    @classmethod
    def get_user_sale_transaction_organizations(cls, user: User, start_date, end_date):
        transactions = cls.get_user_sale_transactions(user=user)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(created_at__range=[start_date, end_date])
        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).annotate(
            latest_transaction_time=Subquery(
                Transaction.objects.filter(
                    Q(organization=OuterRef('pk')) & (
                            (Q(processed_by=user) | Q(status=Transaction.IN_PROGRESS)) & ~Q(
                        Q(status=Transaction.IN_PROGRESS) & Q(type=Transaction.OFFLINE)))).order_by(
                    '-updated_at').values('updated_at')[:1]
            ),
            unprocessed_transaction_count=Count(
                Transaction.objects.filter(organization_id=OuterRef('pk'), type=Transaction.ONLINE,
                                           status=Transaction.IN_PROGRESS).values('id')[:1])
        )

        organizations = organizations.order_by('-unprocessed_transaction_count',
                                               F('latest_transaction_time').desc(nulls_last=True))
        return organizations

    @classmethod
    def get_user_rental_transaction_organizations(cls, client: User, start_date, end_date):
        transactions = Transaction.objects.filter(client=client, is_processed=True, booking__item__purchase_type='rent')

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(created_at__range=[start_date, end_date])

        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).annotate(
            latest_transaction_time=Subquery(
                Transaction.objects.filter(organization=OuterRef('pk'), client=client,
                                           ).order_by('-updated_at').values('updated_at')[:1]
            )
        ).order_by('-latest_transaction_time')
        return organizations

    @classmethod
    def get_user_sale_rental_transaction_organizations(cls, user: User, start_date, end_date):
        transactions = cls.get_user_sale_rental_transactions(user=user)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(created_at__range=[start_date, end_date])
        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).annotate(
            latest_transaction_time=Subquery(
                Transaction.objects.filter(
                    Q(organization=OuterRef('pk')) & (
                            (Q(processed_by=user) | Q(status=Transaction.IN_PROGRESS)) & ~Q(
                        Q(status=Transaction.IN_PROGRESS) & Q(type=Transaction.OFFLINE)))).order_by(
                    '-updated_at').values('updated_at')[:1]
            ),
            unprocessed_transaction_count=Count(
                Transaction.objects.filter(organization_id=OuterRef('pk'), type=Transaction.ONLINE,
                                           status=Transaction.IN_PROGRESS).values('id')[:1])
        )

        organizations = organizations.order_by('-unprocessed_transaction_count',
                                               F('latest_transaction_time').desc(nulls_last=True))
        return organizations

    @classmethod
    def get_user_totals(cls, client: User, currency: str,
                        organization: Organization = None, start_date=None, end_date=None) -> dict:
        transactions = Transaction.objects.filter(client=client, is_processed=True)

        if organization is not None:
            transactions = transactions.filter(organization=organization)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        transactions = transactions.order_by().values('currency').annotate(
            total_spent=Coalesce(Sum('final_amount'), 0),
            total_savings=Coalesce(Sum('savings'), 0),
            total_from_cashback=Coalesce(Sum('from_cashback'), 0)
        )
        return StatisticsService.get_transaction_totals_in_one_currency(totals=transactions, currency=currency)

    @classmethod
    def get_user_sale_totals(cls, processed_by: User, currency: str,
                             organization: Organization = None, start_date=None, end_date=None) -> dict:
        transactions = Transaction.objects.filter(processed_by=processed_by, is_processed=True)

        if organization is not None:
            transactions = transactions.filter(organization=organization)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        transactions = transactions.order_by().values('currency').annotate(
            total_spent=Coalesce(Sum('final_amount'), 0),
            total_savings=Coalesce(Sum('savings'), 0),
            total_from_cashback=Coalesce(Sum('from_cashback'), 0)
        )
        return StatisticsService.get_transaction_totals_in_one_currency(totals=transactions, currency=currency)

    @classmethod
    def get_user_rental_totals(cls, client: User, currency: str,
                        organization: Organization = None, start_date=None, end_date=None) -> dict:
        transactions = Transaction.objects.filter(client=client, is_processed=True, booking__item__purchase_type='rent')

        if organization is not None:
            transactions = transactions.filter(organization=organization)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        transactions = transactions.order_by().values('currency').annotate(
            total_spent=Coalesce(Sum('final_amount'), 0),
            total_savings=Coalesce(Sum('savings'), 0),
            total_from_cashback=Coalesce(Sum('from_cashback'), 0)
        )
        return StatisticsService.get_transaction_totals_in_one_currency(totals=transactions, currency=currency)

    @classmethod
    def get_user_sale_rental_totals(cls, processed_by: User, currency: str,
                             organization: Organization = None, start_date=None, end_date=None) -> dict:
        transactions = Transaction.objects.filter(processed_by=processed_by, is_processed=True,
                                                  booking__item__purchase_type='rent')

        if organization is not None:
            transactions = transactions.filter(organization=organization)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        transactions = transactions.order_by().values('currency').annotate(
            total_spent=Coalesce(Sum('final_amount'), 0),
            total_savings=Coalesce(Sum('savings'), 0),
            total_from_cashback=Coalesce(Sum('from_cashback'), 0)
        )
        return StatisticsService.get_transaction_totals_in_one_currency(totals=transactions, currency=currency)

    @classmethod
    def get_client_total_spent_in_cumulative_group(cls, client: User, organization: Organization,
                                                   currency: str) -> Decimal:
        partner_ids = CumulativeGroupService.get_partners_in_same_cumulative_group(organization=organization)
        partner_ids.append(organization.id)
        transactions = Transaction.objects.filter(
            client=client, is_processed=True, organization_id__in=partner_ids
        ).order_by().values('currency').annotate(total_spent=Coalesce(Sum('final_amount'), 0))

        return StatisticsService.get_total_spent_in_one_currency(totals=transactions, currency=currency)

    @classmethod
    def get_user_transactions(cls, client: User):
        transactions = Transaction.objects.filter(Q(client=client) & ~Q(
            Q(status=Transaction.IN_PROGRESS) & Q(type=Transaction.OFFLINE))).annotate(
            in_progress_first=Case(When(status=Transaction.IN_PROGRESS, then=0),
                                   When(status=Transaction.ACCEPTED, then=1),
                                   When(status=Transaction.REJECTED, then=1), output_field=IntegerField())
        ).order_by('in_progress_first', '-updated_at')

        return transactions

    @classmethod
    def get_organization_follower_transactions(cls, requested_by: User, follower_id: int,
                                               organization_id: int) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        user = User.objects.get(id=follower_id)
        if not MembershipService.has_seller_stats_rights_in_any_organization(user=requested_by,
                                                                             organization=organization):
            raise PermissionDeniedException(_('Permission denied'))

        if not Subscription.objects.filter(user=user, organization=organization).exists():
            raise ObjectNotFoundException(_('Follower not found'))

        transactions = Transaction.objects.filter(organization_id=organization_id, client_id=follower_id)
        return transactions

    @classmethod
    def get_follower(cls, user_id: int, organization_id: int, requested_by: User) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        user = User.objects.get(id=user_id)
        if not MembershipService.is_organization_member_or_owner(user=requested_by, organization=organization):
            raise PermissionDeniedException(_('Permission denied'))

        if not Subscription.objects.filter(user=user, organization=organization).exists():
            raise ObjectNotFoundException(_('Follower not found'))
        return user

    @classmethod
    def get_organization_transactions(cls, organization: Organization, processed_by: User = None,
                                      start_date=None, end_date=None, search_id: int = None, client: User = None):

        transactions = Transaction.objects.filter(Q(organization=organization) & ~Q(
            Q(status=Transaction.IN_PROGRESS) & Q(type=Transaction.OFFLINE))).annotate(
            in_progress_first=Case(When(status=Transaction.IN_PROGRESS, then=0),
                                   When(status=Transaction.ACCEPTED, then=1),
                                   When(status=Transaction.REJECTED, then=1), output_field=IntegerField())
        ).order_by('in_progress_first', '-updated_at')

        if processed_by is not None:
            transactions = transactions.filter(
                Q(processed_by=processed_by) | Q(status=Transaction.IN_PROGRESS))
        if client is not None:
            transactions = transactions.filter(client=client)
        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(
                Q(display_time__range=[start_date, end_date]) | Q(display_time__isnull=True)
            )

        if search_id is not None:
            transactions = transactions.filter(id__contains=search_id)

        return transactions

    @classmethod
    def get_organization_processed_transactions(cls, rental: ShopItem, start_date=None, end_date=None):

        transactions = Transaction.objects.filter(booking__item=rental, is_processed=True,
                                                  booking__item__purchase_type='rent').order_by('-updated_at')

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(
                Q(display_time__range=[start_date, end_date]) | Q(display_time__isnull=True)
            )

        return transactions


    @classmethod
    @transaction.atomic
    def refund_transaction(cls, request, old_transaction: Transaction, user: User):
        if old_transaction.status == Transaction.REJECTED:
            raise BadRequestException(message=_('This transaction already was rejected'))
        from shop.serializers.cart_serializers import CartSerializer
        try:
            fixed_cart = CartSerializer(old_transaction.cart, context={
                'request': request}).data
        except Cart.DoesNotExist:
            fixed_cart = None

        role = OrganizationService.get_user_role_in_organization(organization=old_transaction.organization, user=user)
        try:
            old_transaction.employee_name = user.full_name
            old_transaction.employee_role = role
            if not old_transaction.fixed_cart:
                old_transaction.fixed_cart = fixed_cart
            old_transaction.employee_avatar = user.avatar
            old_transaction.status = Transaction.REJECTED
            old_transaction.is_processed = False
            old_transaction.processed_by = user
            if old_transaction.display_time is None:
                old_transaction.display_time = now()
            old_transaction.save()
        except:
            raise IntegrityException()

        client_status = OrganizationClientFinancialStatusService.get(
            user=old_transaction.client, organization=old_transaction.organization
        )
        if client_status is not None:
            OrganizationClientFinancialStatusService.recalculate_cashback_after_refund(
                client_status=client_status, refunded_transaction=old_transaction
            )
            OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)
        if old_transaction.type == Transaction.ONLINE:
            Notification.objects.filter(
                Q(extra_data__transaction_id=old_transaction.id) & (
                        Q(type=REQUEST_ORDER_TYPE) | Q(type=REQUEST_ORDER_CLIENT_TYPE))).delete()

        discount_percent = old_transaction.discount_percent

        sent_notification.delay(
            recipient_id=user.id,
            sender_id=old_transaction.client_id,
            mode=NOTIFICATION_MODE_PRODUCT,
            notification_type=DECLINE_ORDER_TYPE,
            organization_id=old_transaction.organization_id,
            extra_data=dict(transaction_id=old_transaction.id,
                            total_price=old_transaction.final_amount,
                            discount_percent=discount_percent,
                            currency=old_transaction.currency.code)
        )
        sent_notification.delay(
            recipient_id=old_transaction.client_id,
            sender_id=old_transaction.processed_by_id,
            mode=NOTIFICATION_MODE_PRODUCT,
            notification_type=DECLINE_ORDER_CLIENT_TYPE,
            organization_id=old_transaction.organization_id,
            extra_data=dict(transaction_id=old_transaction.id,
                            total_price=old_transaction.final_amount,
                            discount_percent=discount_percent,
                            currency=old_transaction.currency.code)
        )

    @classmethod
    @transaction.atomic
    def refund_booking_transaction(cls, request, old_transaction: Transaction, user: User):
        from shop.serializers.cart_serializers import BookingSerializer
        try:
            fixed_cart = BookingSerializer(old_transaction.booking, context={
                'request': request}).data
        except Cart.DoesNotExist:
            fixed_cart = None

        role = OrganizationService.get_user_role_in_organization(organization=old_transaction.organization, user=user)
        try:
            old_transaction.employee_name = user.full_name
            old_transaction.employee_role = role
            if not old_transaction.fixed_cart:
                old_transaction.fixed_cart = fixed_cart
            old_transaction.employee_avatar = user.avatar
            old_transaction.status = Transaction.REJECTED
            old_transaction.is_processed = False
            old_transaction.processed_by = user
            if old_transaction.display_time is None:
                old_transaction.display_time = now()
            old_transaction.save()
            booking = old_transaction.booking
            booking.is_open = False
            booking.save()
        except:
            raise IntegrityException()

        client_status = OrganizationClientFinancialStatusService.get(
            user=old_transaction.client, organization=old_transaction.organization
        )
        if client_status is not None:
            OrganizationClientFinancialStatusService.recalculate_cashback_after_refund(
                client_status=client_status, refunded_transaction=old_transaction
            )
            OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)
        if old_transaction.type == Transaction.ONLINE:
            Notification.objects.filter(
                Q(extra_data__transaction_id=old_transaction.id) & (
                        Q(type=ACCEPT_RENTAL_TYPE) | Q(type=ACCEPT_RENTAL_CLIENT_TYPE) |
                        Q(type=REQUEST_RENTAL_TYPE) |Q(type=REQUEST_RENTAL_CLIENT_TYPE))).delete()

        discount_percent = old_transaction.discount_percent
        if old_transaction.status == Transaction.REJECTED and old_transaction.payment_status == Transaction.ACCEPTED:
            if old_transaction.type == Transaction.ONLINE:
                Notification.objects.filter(
                    Q(extra_data__transaction_id=old_transaction.id) & (
                            Q(type=ACCEPT_RENTAL_PAYMENT_TYPE) | Q(type=ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE))).delete()

            try:
                old_transaction.payment_status = Transaction.REFUNDED
                old_transaction.save()
            except:
                raise IntegrityException()
            sent_notification.delay(
                recipient_id=user.id,
                sender_id=old_transaction.client_id,
                mode=NOTIFICATION_MODE_RENTAL,
                notification_type=DECLINE_ACCEPTED_RENTAL_TYPE,
                organization_id=old_transaction.organization_id,
                extra_data=dict(transaction_id=old_transaction.id,
                                total_price=old_transaction.final_amount,
                                discount_percent=discount_percent,
                                currency=old_transaction.currency.code)
            )
            sent_notification.delay(
                recipient_id=old_transaction.client_id,
                sender_id=old_transaction.processed_by_id,
                mode=NOTIFICATION_MODE_RENTAL,
                notification_type=DECLINE_ACCEPTED_RENTAL_CLIENT_TYPE,
                organization_id=old_transaction.organization_id,
                extra_data=dict(transaction_id=old_transaction.id,
                                total_price=old_transaction.final_amount,
                                discount_percent=discount_percent,
                                currency=old_transaction.currency.code)
            )
        else:
            sent_notification.delay(
                recipient_id=user.id,
                sender_id=old_transaction.client_id,
                mode=NOTIFICATION_MODE_RENTAL,
                notification_type=DECLINE_RENTAL_TYPE,
                organization_id=old_transaction.organization_id,
                extra_data=dict(transaction_id=old_transaction.id,
                                total_price=old_transaction.final_amount,
                                discount_percent=discount_percent,
                                currency=old_transaction.currency.code)
            )
            sent_notification.delay(
                recipient_id=old_transaction.client_id,
                sender_id=old_transaction.processed_by_id,
                mode=NOTIFICATION_MODE_RENTAL,
                notification_type=DECLINE_RENTAL_CLIENT_TYPE,
                organization_id=old_transaction.organization_id,
                extra_data=dict(transaction_id=old_transaction.id,
                                total_price=old_transaction.final_amount,
                                discount_percent=discount_percent,
                                currency=old_transaction.currency.code)
            )

    @classmethod
    @transaction.atomic
    def accept_booking_transaction_by_user(cls, request, transaction_id: Transaction, user: User):
        old_transaction = cls.get(id=transaction_id, is_processed=False, status=Transaction.ACCEPTED)
        if old_transaction.client != request.user:
            raise PermissionDeniedException(_('Permission denied'))
        try:
            old_transaction.payment_status = Transaction.ACCEPTED
            old_transaction.is_processed = True
            old_transaction.save()
            booking = old_transaction.booking
            booking.is_open = False
            booking.save()
        except:
            raise IntegrityException()

        old_start_time = old_transaction.booking.start_time
        old_end_time = old_transaction.booking.end_time

        bookings = Booking.objects.filter(
            organization=old_transaction.booking.organization,
            start_time__lt=old_end_time,
            end_time__gt=old_start_time,
            is_open=True
        ).exclude(id=old_transaction.booking.id)

        for booking in bookings:
            if booking.transaction.type == Transaction.ONLINE:
                TransactionService.refund_booking_transaction(old_transaction=booking.transaction, user=booking.organization.owner,
                                                              request=request)

        if old_transaction.type == Transaction.ONLINE:
            Notification.objects.filter(
                Q(extra_data__transaction_id=old_transaction.id) & (
                        Q(type=ACCEPT_RENTAL_TYPE) | Q(type=ACCEPT_RENTAL_CLIENT_TYPE))).delete()

        discount_percent = old_transaction.discount_percent

        sent_notification.delay(
            recipient_id=old_transaction.processed_by_id,
            sender_id=old_transaction.client_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=ACCEPT_RENTAL_PAYMENT_TYPE,
            organization_id=old_transaction.organization_id,
            extra_data=dict(transaction_id=old_transaction.id,
                            total_price=old_transaction.final_amount,
                            discount_percent=discount_percent,
                            currency=old_transaction.currency.code)
        )
        sent_notification.delay(
            recipient_id=old_transaction.client_id,
            sender_id=old_transaction.processed_by_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE,
            organization_id=old_transaction.organization_id,
            extra_data=dict(transaction_id=old_transaction.id,
                            total_price=old_transaction.final_amount,
                            discount_percent=discount_percent,
                            currency=old_transaction.currency.code)
        )

    @classmethod
    @transaction.atomic
    def reject_booking_transaction_by_user(cls, request, old_transaction: Transaction, user: User):
        if old_transaction.client != request.user:
            raise PermissionDeniedException(_('Permission denied'))
        try:
            old_transaction.payment_status = Transaction.REJECTED
            old_transaction.save()
        except:
            raise IntegrityException()
        if old_transaction.type == Transaction.ONLINE:
            Notification.objects.filter(
                Q(extra_data__transaction_id=old_transaction.id) & (
                        Q(type=ACCEPT_RENTAL_TYPE) | Q(type=ACCEPT_RENTAL_CLIENT_TYPE))).delete()

        discount_percent = old_transaction.discount_percent

        sent_notification.delay(
            recipient_id=old_transaction.processed_by_id,
            sender_id=old_transaction.client_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=DECLINE_RENTAL_PAYMENT_TYPE,
            organization_id=old_transaction.organization_id,
            extra_data=dict(transaction_id=old_transaction.id,
                            total_price=old_transaction.final_amount,
                            discount_percent=discount_percent,
                            currency=old_transaction.currency.code)
        )

        sent_notification.delay(
            recipient_id=old_transaction.client_id,
            sender_id=old_transaction.processed_by_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=DECLINE_RENTAL_PAYMENT_CLIENT_TYPE,
            organization_id=old_transaction.organization_id,
            extra_data=dict(transaction_id=old_transaction.id,
                            total_price=old_transaction.final_amount,
                            discount_percent=discount_percent,
                            currency=old_transaction.currency.code)
        )

    @classmethod
    def get_unprocessed_transactions_count(cls, user: User):
        memberships = Membership.objects.filter(
            Q(user=user) & (Q(role__can_sale=True) | Q(role__can_see_stats=True) | Q(role__can_edit_organization=True)))
        organization = Organization.objects.filter(Q(memberships__in=memberships) | Q(owner=user))
        return Transaction.objects.filter(organization__in=organization,
                                          status=Transaction.IN_PROGRESS, type=Transaction.ONLINE).count()

    @classmethod
    def get_user_sale_transactions(cls, user: User):
        memberships = Membership.objects.filter(
            Q(user=user) & (Q(role__can_sale=True) | Q(role__can_see_stats=True) | Q(role__can_edit_organization=True)))
        organization = Organization.objects.filter(Q(memberships__in=memberships) | Q(owner=user))
        #
        # transactions = Transaction.objects.filter(
        #     (Q(processed_by=user) & Q(organization__in=organization)) | (
        #             Q(organization__in=organization) & Q(status=Transaction.IN_PROGRESS)))
        #
        # (a & b) | (a & c) = a & (b | c)
        # a = Q(organization__in=organization)
        # b = Q(processed_by=user)
        # c = Q(status=Transaction.IN_PROGRESS)
        # (Q(organization__in=organization) & Q(processed_by=user)) |
        #     (Q(organization__in=organization) & Q(status=Transaction.IN_PROGRESS))
        # ==
        # Q(organization__in=organization) & (Q(processed_by=user) | Q(status=Transaction.IN_PROGRESS))
        transactions = Transaction.objects.filter(
            Q(organization__in=organization) & (
                    Q(processed_by=user) | Q(status=Transaction.IN_PROGRESS) | Q(status=Transaction.ACCEPTED))
        )
        return transactions

    @classmethod
    def get_user_sale_rental_transactions(cls, user: User):
        memberships = Membership.objects.filter(
            Q(user=user) & (Q(role__can_sale=True) | Q(role__can_see_stats=True) | Q(role__can_edit_organization=True)))
        organization = Organization.objects.filter(Q(memberships__in=memberships) | Q(owner=user))

        transactions = Transaction.objects.filter(
            Q(booking__item__purchase_type='rent') &
            Q(organization__in=organization) &
            (
                Q(processed_by=user) |
                Q(status__in=[Transaction.IN_PROGRESS, Transaction.ACCEPTED])
            )
        )

        return transactions

    @classmethod
    def get_users_of_transactions_in_organization(cls, organization: Organization, processed_by: User) -> QuerySet:
        transactions = cls.get_organization_transactions(organization=organization,
                                                         processed_by=processed_by)

        return User.objects.filter(
            bought_transactions__in=transactions).annotate(max_date=Max('bought_transactions__created_at')).order_by(
            '-max_date')

    @classmethod
    def get_ordering_search_result(cls, queryset: QuerySet, search_word: str) -> QuerySet:
        queryset = queryset.filter(client__full_name__icontains=search_word).annotate(
            search_rank=Case(
                When(client__full_name__iexact=search_word, then=Value(1)),
                When(client__full_name__istartswith=search_word, then=Value(2)),
                When(client__full_name__icontains=search_word, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            ),
        ).order_by('search_rank', '-created_at')

        return queryset


    @classmethod
    def activate_rental(cls, transaction: Transaction):
        transaction = cls.get(id=transaction.id)
        booking = transaction.booking
        if booking.is_active:
            raise BadRequestException(message=_('This rental already was activated'))
        try:
            booking.is_active = True
            booking.save()
        except:
            raise IntegrityException()

        extra_data = {
            'transaction_id': transaction.id,
            'total_price': transaction.final_amount,
            'discount_percent': transaction.discount_percent,
            'currency': transaction.currency.code
        }

        sent_notification.delay(
            recipient_id=transaction.client_id,
            sender_id=transaction.processed_by_id,
            mode=NOTIFICATION_MODE_RENTAL,
            notification_type=ACTIVATE_RENTAL_CLIENT_TYPE,
            organization_id=transaction.organization_id,
            extra_data=extra_data
        )
