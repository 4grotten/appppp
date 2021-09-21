from urllib.parse import urlparse

from django.contrib.gis.db.models import PointField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.models import TimestampModel, Currency, Country, City
from organizations.constants import HOTLINK_TYPES, HOTLINK_URL, HOTLINK_INTERNAL_LINK_DOMAINS, HOTLINK_PARTNERS
from organizations.managers import ActiveOrganizationManager, OrganizationManager
from users.models import User


class CashbackGroup(TimestampModel):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.name}'


class CumulativeGroup(TimestampModel):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.name}'


class CommonItemsGroup(TimestampModel):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.name}'


class OrganizationCategory(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = _('Organization categories')
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}'


class OrganizationType(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(OrganizationCategory, on_delete=models.CASCADE, related_name='types')
    is_adult = models.BooleanField(default=False)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return f'{self.title}'


class Organization(TimestampModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_organizations')

    title = models.CharField(max_length=255)
    title_lang = models.CharField(max_length=8, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    description_lang = models.CharField(max_length=8, null=True, blank=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='organizations', default='KGS')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='organizations', default='KG')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, related_name='organizations', null=True)
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='organizations')
    show_contacts = models.BooleanField(default=False)
    types = models.ManyToManyField(OrganizationType, blank=True, related_name='organizations')
    address = models.CharField(max_length=255, null=True, blank=True)
    location = PointField(help_text="Для создания местоположения", null=True, blank=True)

    cashback_group = models.ForeignKey(CashbackGroup, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='organizations')
    cumulative_group = models.ForeignKey(CumulativeGroup, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='organizations')
    items_group = models.ForeignKey(CommonItemsGroup, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='organizations')
    running_purchase_id = models.PositiveIntegerField(default=1, help_text=_('For transaction purchase ids'))

    has_delivery = models.BooleanField(default=True, help_text=_('Does organization have courier delivery?'))
    has_self_pick_up = models.BooleanField(default=True, help_text=_('Does organization have self pick up?'))

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    is_delivery_service = models.BooleanField(default=False)
    is_bank = models.BooleanField(default=False)

    # Managers
    objects = OrganizationManager()
    active_organizations = ActiveOrganizationManager()

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return f'{self.title}'

    @property
    def full_location(self):
        full_location = dict(
            latitude=None if not self.location or not self.location.y else self.location.y,
            longitude=None if not self.location or not self.location.x else self.location.x
        )
        return full_location


class PhoneNumber(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.phone_number}'


class SocialNetworkContact(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='social_contacts')
    url = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.url}'


class InstagramIntegration(TimestampModel):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE,
                                        related_name='instagram_integration_link')
    url = models.URLField(max_length=255)
    account_full_name = models.CharField(null=True, blank=True, max_length=50)
    account_user_name = models.CharField(null=True, blank=True, max_length=50)
    account_user_id = models.CharField(null=True, blank=True, max_length=50)
    profile_photo = models.URLField(null=True, max_length=500)
    avatar = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='instagram_integrations')

    def __str__(self):
        return f'{self.url}'


class Role(models.Model):
    title = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='roles')
    can_sale = models.BooleanField(default=False)
    can_check_attendance = models.BooleanField(default=False)
    can_see_stats = models.BooleanField(default=False)
    can_edit_organization = models.BooleanField(default=False)
    can_send_message = models.BooleanField(default=True)
    can_edit_partner = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title} in {self.organization.title}'


class Membership(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='memberships')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='added_memberships')

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f'{self.user} as {self.role} in {self.organization}'


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='attendances')
    arrival_time = models.DateTimeField(auto_now_add=True)
    arrival_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='checked_arrivals')
    arrival_checker_role = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    departure_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='checked_departures')
    departure_checker_role = models.CharField(max_length=255, null=True, blank=True)
    organization_name = models.CharField(max_length=255, null=True, blank=True)

    # TODO organization name saving

    def __str__(self):
        return f'{self.user} came to {self.organization.title} at {self.arrival_time}'

    class Meta:
        ordering = ('-arrival_time',)


class DiscountCard(TimestampModel):
    FIXED = 'fixed'
    CUMULATIVE = 'cumulative'
    CASHBACK = 'cashback'
    TYPES = (
        (FIXED, FIXED),
        (CUMULATIVE, CUMULATIVE),
        (CASHBACK, CASHBACK),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='discounts')
    type = models.CharField(max_length=20, choices=TYPES, default=FIXED)
    percent = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='discounts', null=True, blank=True)
    limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)

    next_cumulative = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='previous_cumulative')

    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ('organization', 'type', 'limit', 'percent',)
        constraints = [
            models.UniqueConstraint(fields=('organization', 'type', 'percent'), name='unique_percents_of_organization'),
            models.UniqueConstraint(fields=('organization', 'type', 'limit'), name='unique_limits_of_organization'),
        ]

    def __str__(self):
        return f'{self.percent}% {self.type} card in {self.organization.title}'

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        errors = {}

        if self.type == self.CUMULATIVE:
            if not self.currency:
                errors['currency'] = _('This field is required')
            if not self.limit:
                errors['limit'] = _('This field is required')

        if errors:
            raise ValidationError(errors)


class CardBackground(models.Model):
    image = models.ForeignKey('common.File', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='backgrounds')

    def __str__(self):
        return f'Card background #{self.id}: {self.image}'


class OrganizationClientFinancialStatus(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cards')
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='client_statuses')
    card = models.ForeignKey(DiscountCard, on_delete=models.PROTECT, related_name='clients', null=True, blank=True)
    accrued_cashback = models.DecimalField(max_digits=16, decimal_places=2, default=0,
                                           validators=[MinValueValidator(0)])

    def __str__(self):
        return f'{self.user} status in {self.organization.title}'

    class Meta:
        verbose_name_plural = _('Organization client financial statuses')
        constraints = [
            models.UniqueConstraint(fields=('user', 'organization'), name='unique_statuses_of_user_in_organization')
        ]


class Subscription(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f'{self.user} subscribed to {self.organization}'


class Partnership(TimestampModel):
    requested_by = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='requested_partnerships')
    accepted_by = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='accepted_partnerships')

    is_accepted = models.BooleanField(default=False)

    can_check_attendance = models.BooleanField(default=False)
    can_see_stats = models.BooleanField(default=False)
    can_edit_organization = models.BooleanField(default=False)
    can_share_cashback = models.BooleanField(default=False)
    can_share_cumulative = models.BooleanField(default=False)
    can_share_items = models.BooleanField(default=False)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('requested_by', 'accepted_by'), name='unique_partnerships'),
        )

    def __str__(self):
        return f'{self.accepted_by} accepted partnership of {self.requested_by}'


class Banner(TimestampModel):
    host_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='hosted_banners')
    linked_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='leading_banners')

    image = models.ForeignKey('common.File', on_delete=models.CASCADE, related_name='banners')

    def __str__(self):
        return f'Banner of {self.linked_organization} hosted by {self.host_organization}'


class Message(TimestampModel):
    ORGANIZATION_FOLLOWERS = 'organization_followers'
    PARTNERS_MEMBERS = 'partners_members'
    PARTNERS_SUBSCRIPTIONS = 'partners_followers'
    MESSAGE_TO = (
        (ORGANIZATION_FOLLOWERS, ORGANIZATION_FOLLOWERS),
        (PARTNERS_MEMBERS, PARTNERS_MEMBERS),
        (PARTNERS_SUBSCRIPTIONS, PARTNERS_SUBSCRIPTIONS)
    )
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sent_messages')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization_messages')
    content = models.CharField(blank=False, null=False, max_length=800)
    message_to = models.CharField(max_length=50, choices=MESSAGE_TO, default=ORGANIZATION_FOLLOWERS)
    receivers = models.ManyToManyField(User, related_name='received_messages')
    organization_address = models.CharField(max_length=255, null=True)
    receiver_partners = models.ManyToManyField(Organization, related_name='receiver_partners')

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Message of {self.organization.title}'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.pk:
            self.organization_address = self.organization.address
        super(Message, self).save()


class Hotlink(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='hotlinks')
    content = models.CharField(max_length=500)
    link_type = models.CharField(max_length=25, choices=HOTLINK_TYPES)
    image = models.ForeignKey('common.File', on_delete=models.CASCADE, related_name='hotlinks')
    linked_item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='hotlinks_to_organization')
    linked_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='hotlinks_to_organization')

    def __str__(self):
        return f'#{self.id} | Hotlink of {self.organization}'

    def save(self, *args, **kwargs):
        parsed_link = urlparse(self.content)
        is_internal = False

        if (self.link_type == HOTLINK_URL or self.link_type == HOTLINK_PARTNERS) and parsed_link.netloc in HOTLINK_INTERNAL_LINK_DOMAINS:
            if parsed_link.path.startswith('/p/'):
                item_id = parsed_link.path.replace('/p/', '').replace('/', '')
                from shop.models import ShopItem
                try:
                    linked_item = ShopItem.objects.get(id=item_id)
                    self.linked_item = linked_item
                    self.linked_organization = None
                    is_internal = True
                except ShopItem.DoesNotExist:
                    pass
            elif parsed_link.path.startswith('/organizations/'):
                organization_id = parsed_link.path.replace('/organizations/', '').replace('/', '')
                try:
                    linked_organization = Organization.objects.get(id=organization_id)
                    self.linked_organization = linked_organization
                    self.linked_item = None
                    is_internal = True
                except Organization.DoesNotExist:
                    pass
            elif parsed_link.path.startswith('/home/partners/'):
                organization_id = parsed_link.path.replace('/home/partners/', '').replace('/', '')
                try:
                    linked_organization = Organization.objects.get(id=organization_id)
                    self.linked_organization = linked_organization
                    self.linked_item = None
                    self.link_type = HOTLINK_PARTNERS
                    is_internal = True
                except Organization.DoesNotExist:
                    pass

        if not is_internal:
            self.linked_item_id = None
            self.linked_organization = None
            self.linked_item = None

        super().save(*args, **kwargs)


class HotlinkCollectionItem(TimestampModel):
    hotlink = models.ForeignKey(Hotlink, on_delete=models.CASCADE, related_name='collection_items')
    item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE, related_name='hotlinks')

    def __str__(self):
        return f'{self.item} in collection {self.hotlink.content}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('hotlink', 'item'), name='one_item_per_hotlink_collection')
        ]


class HotlinkCollectionSubcategory(TimestampModel):
    hotlink = models.ForeignKey(Hotlink, on_delete=models.CASCADE, related_name='collection_subcategories')
    subcategory = models.ForeignKey('shop.ItemSubcategory', on_delete=models.CASCADE, related_name='hotlinks')

    def __str__(self):
        return f'{self.subcategory} in collection {self.hotlink.content}'

    class Meta:
        verbose_name_plural = _('hotlink collection subcategories')
        constraints = [
            models.UniqueConstraint(fields=('hotlink', 'subcategory'), name='one_subcategory_per_hotlink_collection')
        ]


class HotlinkCollectionLink(TimestampModel):
    hotlink = models.ForeignKey(Hotlink, on_delete=models.CASCADE, related_name='collection_links')
    content = models.CharField(max_length=500)
    linked_item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE, related_name='links_in_collections')

    def __str__(self):
        return f'{self.linked_item} in collection {self.hotlink.content}'

    def save(self, *args, **kwargs):
        parsed_link = urlparse(self.content)

        if parsed_link.netloc not in HOTLINK_INTERNAL_LINK_DOMAINS:
            raise NotAcceptableException(_('Wrong url for shop item'))
        if not parsed_link.path.startswith('/p/'):
            raise NotAcceptableException(_('Wrong url for shop item'))

        item_id = parsed_link.path.replace('/p/', '').replace('/', '')
        from shop.models import ShopItem
        try:
            linked_item = ShopItem.objects.get(id=item_id)
            self.linked_item = linked_item
        except ValueError:
            raise NotAcceptableException(_('Wrong url for shop item'))
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item with given id is not found'))

        super().save(*args, **kwargs)


class OrganizationPromo(TimestampModel):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='promo')
    total_cashback = models.DecimalField(max_digits=16, decimal_places=2,
                                         validators=([MinValueValidator(0), MaxValueValidator(999999999)]))
    cashback = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(0)])
    granted_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    image = models.ForeignKey('common.File', on_delete=models.CASCADE, related_name='org_promos')

    def __str__(self):
        return f'{self.organization} cashback promo'


class PromoEditLog(models.Model):
    promo = models.ForeignKey(OrganizationPromo, on_delete=models.CASCADE, related_name='edit_logs')
    created_at = models.DateTimeField(auto_now_add=True)

    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_edit_logs')
    employee_name = models.CharField(max_length=255, null=True, blank=True)
    employee_role = models.CharField(max_length=255, null=True)
    employee_avatar = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.changed_by} edited {self.promo}'


class PromoSubscriber(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='promo_subscribers')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_subscriptions')
    cashback = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.constraints.UniqueConstraint(fields=('organization', 'subscriber'), name='unique_promo_subscriber'),
        )
