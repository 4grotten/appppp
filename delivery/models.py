from django.contrib.gis.db.models import PointField
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampModel, Country, City, Currency
from organizations.models import Organization
from transactions.models import Transaction


class DeliveryInfo(TimestampModel):
    DELIVERY_STATUS_OWN_DELIVERY = 'delivery_status_set_for_own_delivery'
    DELIVERY_STATUS_TAKEN_FOR_DELIVERY = 'delivery_status_taken_for_delivery'
    DELIVERY_STATUS_SET_FOR_DELIVERY = 'delivery_status_set_for_delivery'
    DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE = 'delivery_status_rejected_by_delivery_service'
    DELIVERY_STATUS_ACCEPTED_BY_DELIVERY_SERVICE = 'delivery_status_accepted_by_delivery_service'
    DELIVERY_STATUS_DELIVERED = 'delivery_status_delivered'
    DELIVERY_STATUS_REJECTED_BY_CUSTOMER = 'delivery_status_rejected_by_customer'

    DELIVERY_STATUSES = (
        (DELIVERY_STATUS_TAKEN_FOR_DELIVERY, _("Taken for delivery")),
        (DELIVERY_STATUS_SET_FOR_DELIVERY, _("Set for delivery")),
        (DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE, _("Rejected by delivery service")),
        (DELIVERY_STATUS_ACCEPTED_BY_DELIVERY_SERVICE, _("Accepted by delivery service")),
        (DELIVERY_STATUS_DELIVERED, _("Delivered")),
        (DELIVERY_STATUS_REJECTED_BY_CUSTOMER, _("Rejected by customer")),
    )
    DELIVERY_WHO_PAYS_OWN = 'organization'
    DELIVERY_WHO_PAYS_CLIENT = 'client'

    DELIVERY_WHO_PAYS = (
        (DELIVERY_WHO_PAYS_OWN, _("Organization pays")),
        (DELIVERY_WHO_PAYS_CLIENT, _("Client pays")),

    )
    who_pays = models.CharField(max_length=255, choices=DELIVERY_WHO_PAYS, null=True)
    delivery_organization = models.ForeignKey(Organization, null=True, related_name='delivery_infos',
                                              on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='delivery_infos', default='KG')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, related_name='delivery_infos', null=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, related_name='delivery_info')
    address = models.CharField(max_length=225)
    apartment = models.CharField(max_length=36, null=True, blank=True)
    intercom = models.CharField(max_length=36, null=True, blank=True)
    entrance = models.CharField(max_length=36, null=True, blank=True)
    floor = models.CharField(max_length=36, null=True, blank=True)
    phone = models.CharField(max_length=36)
    comment = models.CharField(max_length=150, null=True, blank=True)
    location = PointField(help_text=_("Customer location coordinates"), null=True, blank=True)
    status = models.CharField(max_length=255, choices=DELIVERY_STATUSES, default=None, null=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, default=200)
    currency = models.ForeignKey(Currency, null=True, on_delete=models.SET_NULL, default="KGS")

    def __str__(self):
        return f'Delivery info of {self.transaction.client}'

    @property
    def full_location(self):
        if self.location and self.location.y and self.location.x:
            return dict(
                latitude=self.location.y,
                longitude=self.location.x
            )
        return None


class DeliveryOrganizationProfile(models.Model):
    class Meta:
        pass
