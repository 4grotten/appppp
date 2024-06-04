from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db.models import PointField

from common.models import TimestampModel, File, FileVideo, Currency, Country
from common.utils import upload_file_with_unique_name
from organizations.models import Organization
from stock.models import CriteriaSubcategory, SizeFormat
from transactions.models import Transaction
from users.constants import GENDER_CHOICES
from users.models import User
from utils.translator import GoogleTranslator


class ItemCategory(models.Model):
    PRODUCT = 'product'
    RENTAL = 'rent'
    TICKET = 'ticket'
    RESUME = 'resume'
    TYPE_CHOICES = (
        (PRODUCT, PRODUCT),
        (RENTAL, RENTAL),
        (TICKET, TICKET),
        (RESUME, RESUME)
    )
    name = models.CharField(max_length=64)
    icon = models.OneToOneField(File, on_delete=models.SET_NULL, null=True, blank=True)
    is_adult = models.BooleanField(default=False)
    purchase_type = models.CharField(max_length=55, choices=TYPE_CHOICES, default='product', null=True, blank=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = _('Item categories')


class ItemSubcategory(models.Model):
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=64)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='item_categories')
    criteria_subcategory = models.ManyToManyField(CriteriaSubcategory, blank=True, related_name='item_subcategories')

    def __str__(self):
        return f'{self.name}: {self.category.name}'

    class Meta:
        verbose_name_plural = _('Item subcategories')
        ordering = ('-organization', 'name',)


class RentalPeriod(models.Model):
    time_choices = (
        ('minute', 'minute'),
        ('hour', 'hour'),
        ('day', 'day'),
        ('month', 'month'),
        ('year', 'year'),
    )
    rent_time_type = models.CharField(max_length=55, choices=time_choices, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def str(self):
        return f'{self.start_date} - {self.end_date}, {self.start_time} - {self.end_time}'


class TicketPeriod(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def str(self):
        return f'{self.start_date} - {self.end_date}, {self.start_time} - {self.end_time}'


class ShopItem(models.Model):
    PRODUCT = 'product'
    RENTAL = 'rent'
    TICKET = 'ticket'
    RESUME = 'resume'
    TYPE_CHOICES = (
        (PRODUCT, PRODUCT),
        (RENTAL, RENTAL),
        (TICKET, TICKET),
        (RESUME, RESUME)
    )
    updated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='shop_items',
                                     null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_shop_items', null=True, blank=True)
    subcategory = models.ForeignKey(ItemSubcategory, on_delete=models.SET_NULL, related_name='items_in_category',
                                    null=True, blank=True)
    name = models.CharField(max_length=255)
    name_lang = models.CharField(max_length=5, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    description_lang = models.CharField(max_length=5, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    article = models.CharField(max_length=64, null=True, blank=True)
    instagram_link = models.URLField(null=True, blank=True)
    images = models.ManyToManyField(File, blank=True, related_name='shop_items')
    videos = models.ManyToManyField(FileVideo, blank=True, related_name='shop_items')
    youtube_links = models.JSONField(null=True, blank=True)
    is_updated = models.BooleanField(default=False)
    removed_at = models.DateTimeField(default=None, blank=True, null=True)

    is_published = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)
    comments_disabled = models.BooleanField(default=False)

    minimum_purchase = models.PositiveIntegerField(null=True, blank=True)
    available_sizes = models.ManyToManyField(SizeFormat, related_name='shop_items', blank=True)

    purchase_type = models.CharField(max_length=55, choices=TYPE_CHOICES, default='product', null=True, blank=True)

    address = models.CharField(max_length=255, null=True, blank=True)
    location = PointField(help_text="Для создания местоположения", null=True, blank=True)

    rental_period = models.ForeignKey(RentalPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    ticket_period = models.ForeignKey(TicketPeriod, on_delete=models.SET_NULL, null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='shop_items', null=True, blank=True)
    salary_from = models.PositiveIntegerField(null=True, blank=True)
    salary_to = models.PositiveIntegerField(null=True, blank=True)
    citizenship = models.ManyToManyField(Country, related_name='shop_items', blank=True)
    education = models.ManyToManyField("shop.Education", related_name='shop_items', blank=True)
    current_locations = models.JSONField(null=True, blank=True)
    preferred_locations = models.JSONField(null=True, blank=True)
    links = models.JSONField(null=True, blank=True)


    @property
    def full_location(self):
        full_location = dict(
            latitude=None if not self.location or not self.location.y else self.location.y,
            longitude=None if not self.location or not self.location.x else self.location.x
        )
        return full_location

    @property
    def liked_users_list(self):
        return [like.user.id for like in self.liked_users.all()]

    @property
    def comment_count_list(self):
        return [comment.id for comment in self.comments.all()]

    @property
    def bookmarked_users_list(self):
        return [bookmarked.user.id for bookmarked in self.bookmarked_users.all()]

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.name_lang = GoogleTranslator().get_lang(self.name)
        if self.description:
            self.description_lang = GoogleTranslator().get_lang(self.description)
        if self.price is not None:
            self.discounted_price = self.price * (100 - self.discount) / 100
        if self.subcategory is not None and self.subcategory.category.is_adult:
            self.is_hidden = True
        else:
            self.is_hidden = False
        super().save(*args, **kwargs)


class ResumeInfoFile(TimestampModel):
    order = models.PositiveSmallIntegerField(default=0, editable=False)
    file = models.FileField(upload_to=upload_file_with_unique_name,
                             help_text=_('File that you want to store'),
                             null=True, blank=True)

    @property
    def name(self):
        return self.file.name.split("/")[-1]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(ResumeInfoFile, self).save()

    class Meta:
        ordering = ('order',)


class ResumeInfo(TimestampModel):
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE, related_name='resume_info')
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name='Full Name', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    languages = models.JSONField(null=True, blank=True)
    files = models.ManyToManyField(ResumeInfoFile, blank=True, related_name='resume_info')

    def __str__(self):
        return f"ResumeInfo of {self.item}"


class ResumePhoneNumber(TimestampModel):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='resume_phone_numbers')
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return self.phone_number


class ResumeSocialNetwork(TimestampModel):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='resume_social_networks')
    url = models.CharField(max_length=255)

    def __str__(self):
        return self.url


class ResumeDetailInfo(TimestampModel):
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE, related_name='resume_detail_info')
    text = models.TextField()

    def __str__(self):
        return self.text


class Education(TimestampModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ResumeWorkExperience(TimestampModel):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='resume_work_experience')
    company_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    text = models.TextField()
    start_of_work = models.DateField(null=True)
    end_of_work = models.DateField(null=True)
    up_to_now = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name


class ResumeEducation(TimestampModel):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='resume_education')
    school_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    text = models.TextField()
    start_of_study = models.DateField(null=True)
    end_of_study = models.DateField(null=True)
    up_to_now = models.BooleanField(default=False)

    def __str__(self):
        return self.school_name


class ItemInstagramData(TimestampModel):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='instagram_data')
    thumbnail_url = models.URLField(max_length=5000)
    video_url = models.URLField(max_length=5000, null=True, blank=True)

    def __str__(self):
        return f'Data for {self.item}'


class ItemLike(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_items')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='liked_users')

    def __str__(self):
        return f'{self.user} liked {self.item.name}'

    class Meta:
        constraints = (
            models.constraints.UniqueConstraint(fields=('user', 'item'), name='unique_user_item_like'),
        )


class ItemBookmark(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarked_items')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='bookmarked_users')

    def __str__(self):
        return f'{self.user} bookmarked {self.item.name}'

    class Meta:
        constraints = (
            models.constraints.UniqueConstraint(fields=('user', 'item'), name='unique_user_item_bookmark'),
        )


class ItemCollection(TimestampModel):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='item_collections')
    items = models.ManyToManyField(ShopItem, related_name='collections', blank=True)
    image = models.ForeignKey(ShopItem, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='collection_images')

    def __str__(self):
        return f"Collection '{self.name}' of user {self.user}"


class Cart(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='carts')
    is_open = models.BooleanField(default=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, related_name='cart', null=True)

    def __str__(self):
        return f'Cart of {self.user} in {self.organization}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('organization', 'user'), condition=Q(is_open=True),
                                    name='unique_cart_for_user_in_organization')
        ]


class CartItem(TimestampModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='user_carts')
    count = models.PositiveSmallIntegerField(default=0)
    size = models.ForeignKey('stock.SizeFormat', null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='cart_item')

    def __str__(self):
        return f'Item #{self.item.id} in cart of {self.cart.user}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('cart', 'item', 'size'), name='unique_item_in_user_cart')
        ]
        ordering = ['-created_at']


class Booking(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='bookings')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='user_bookings', null=True, blank=True)
    is_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, related_name='booking', null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)


    def __str__(self):
        return f'Booking of {self.user} in {self.organization}'


class Ticket(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization_ticket')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='user_tickets', null=True, blank=True)
    is_active = models.BooleanField(default=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, related_name='ticket', null=True)

    def __str__(self):
        return f'Ticket of {self.user} in {self.organization}'


class ResumeRequest(TimestampModel):
    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    ACCEPTED = 'accepted'

    STATUS = (
        (IN_PROGRESS, IN_PROGRESS),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED),
    )
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processed_resume',
                                     null=True, blank=True)
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender_user_resume',
                                    null=True, blank=True)
    sender_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='sender_organization_resume')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization_resume')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='item_resumes', null=True, blank=True)
    show_contacts = models.BooleanField(default=True)
    phone_numbers = models.JSONField(null=True, blank=True)
    links = models.JSONField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=20, default=IN_PROGRESS)

    def __str__(self):
        if self.sender_user:
            return f'Resume Request of {self.sender_user} in {self.organization}'
        return f'Resume Request of {self.sender_organization} in {self.organization}'


class Complaint(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='complaints')
    reason = models.TextField(max_length=800)

    def __str__(self):
        return f'Complaint of {self.user} about {self.item.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'item'), name='unique_complaint_from_user')
        ]


class Comment(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, blank=True, null=True
    )
    text = models.TextField(max_length=2000)

    def __str__(self):
        return f'Comment of {self.user} about {self.item.name}'


class CommentLike(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_comments')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='liked_comments')

    def __str__(self):
        return f'{self.user} liked comment with id: {self.comment.id}'

    class Meta:
        constraints = (
            models.constraints.UniqueConstraint(fields=('user', 'comment'), name='unique_user_comment_like'),
        )


class CommentComplaint(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_complaints')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_complaints')
    reason = models.TextField(max_length=800)

    def __str__(self):
        return f'Complaint of {self.user} about {self.comment.text}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'comment'), name='unique_comment_complaint_from_user')
        ]
