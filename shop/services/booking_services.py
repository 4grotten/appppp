import ast
from decimal import Decimal
from shop.models import Booking, ShopItem
from typing import Tuple, Optional, Union
from common.exceptions import (
    ObjectNotFoundException, PermissionDeniedException, IntegrityException, BadRequestException, NotAcceptableException,
    StockException
)
from django.db.models.functions import Coalesce
from notifications.constants import (
    NOTIFICATION_MODE_PRODUCT, REQUEST_ORDER_CLIENT_TYPE, REQUEST_ORDER_TYPE, ACCEPT_ORDER_TYPE,
    NOTIFICATION_MODE_RENTAL, REQUEST_RENTAL_CLIENT_TYPE, REQUEST_RENTAL_TYPE
)
from notifications.tasks import sent_notification, send_notifications_organization_members
from django.db.models import F, Sum, DecimalField
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from transactions.models import Transaction
from users.models import User

class BookingService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Booking.objects.get(*args, **kwargs)
        except Booking.DoesNotExist:
            raise ObjectNotFoundException(_('Booking not found'))

    @classmethod
    def process_booking(cls, user: User, booking_id: int):
        booking = cls.get(id=booking_id)
        if booking.user != user:
            raise PermissionDeniedException(_('No rights to change this booking'))
        if not booking.is_open:
            raise BadRequestException(_('Booking is already closed'))

        current_transaction = cls.create_booking_transaction(booking)
        booking.is_open = False
        try:
            booking.save()
        except IntegrityError:
            raise IntegrityException(_('Could not add transaction'))
        finally:
            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                mode=NOTIFICATION_MODE_RENTAL,
                notification_type=REQUEST_RENTAL_CLIENT_TYPE,
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id,
                                total_price=str(current_transaction.final_amount),
                                currency=current_transaction.currency.code)
            )
            send_notifications_organization_members.delay(
                members_organization_id=current_transaction.organization_id,
                mode=NOTIFICATION_MODE_RENTAL,
                sender_id=current_transaction.client_id,
                with_permissions=dict(can_see_stats=True),
                notification_type=REQUEST_RENTAL_TYPE,
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id,
                                total_price=str(current_transaction.final_amount),
                                currency=current_transaction.currency.code)
            )
            return booking


    @classmethod
    def create_booking_transaction(cls, booking: Booking):
        with transaction.atomic():
            original_price, discounted_price = cls.get_total_prices_in_booking(booking)
            tr, _ = Transaction.objects.get_or_create(
                booking=booking,
                client=booking.user,
                defaults={
                    "organization": booking.organization,
                    "type": Transaction.ONLINE,
                    "original_amount": original_price,
                    "currency": booking.organization.currency,
                    "status": Transaction.IN_PROGRESS,
                    "savings": original_price - discounted_price
                }
            )
            return tr

    @classmethod
    def get_total_prices_in_booking(cls, booking: Booking) -> Tuple[Decimal, Decimal]:
        start_time = booking.start_time
        end_time = booking.end_time
        item = ShopItem.objects.filter(id=booking.item.id)
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
        return totals['original_price'], totals['discounted_price']
