from datetime import datetime
from typing import Tuple, Union

from django.contrib.gis.geos import Point
from django.db import transaction, IntegrityError
from django.db.models import QuerySet, Count, Q, F, Value, ExpressionWrapper, Case, When, IntegerField, TimeField,\
    CharField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.exceptions import (
    ObjectNotFoundException, ValidationException, IntegrityException, NotAcceptableException, PermissionDeniedException,
    BadRequestException
)
from common.models import Country, City, File, Currency
from instagram_parsers.parsers.get_id import get_username_from_instagram_url
from instagram_parsers.parsers.user_info import get_instagram_user_info
from notifications.constants import (
    NOTIFICATION_MODE_SYSTEM, NEW_ORGANIZATION, NEW_ORGANIZATION_TITLE, ORGANIZATION_MESSAGE_TYPE,
    NOTIFICATION_MODE_PERSONAL,
    ORGANIZATION_OWN_TYPE, ORGANIZATION_GAVE_TYPE, ORGANIZATION_GAVE_DESCRIPTION, ORGANIZATION_MESSAGE_SENDER_TYPE,
)
from notifications.tasks import (
    send_notifications_to_all_users, sent_notification, send_notifications_organization_members
)
from organizations.constants import (
    HOMEPAGE_BANNERS_COUNT, HOMEPAGE_MIN_PARTNERS_THRESHOLD, HOMEPAGE_PARTNERS_COUNT,
    HOMEPAGE_MIN_ORDERED_PARTNERS_THRESHOLD, MAX_ORGANIZATIONS_PER_USER
)
from organizations.models import (
    Organization, OrganizationCategory, PhoneNumber, SocialNetworkContact, Message, Subscription, Membership, Role,
    Partnership, InstagramIntegration, Service
)
from organizations.services.membership_services import MembershipService
from organizations.tasks import delete_not_updated_posts_from_instagram, parse_instagram_to_shop_items
from transactions.models import Transaction
from users.models import User
from utils.translator import GoogleTranslator


class OrganizationService:
    model = Organization

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get(cls, *args, **kwargs) -> Organization:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Organization not found'))

    @classmethod
    def creation_limit_exceeded(cls, user: User) -> bool:
        if user.is_staff:
            return False
        return user.owned_organizations.count() >= MAX_ORGANIZATIONS_PER_USER

    @classmethod
    def is_delivery_service(cls, user: User) -> bool:
        queryset = user.owned_organizations.filter(is_delivery_service=True, is_active=True,
                                                   is_banned=False, is_deleted=False)
        if not queryset.count():
            queryset = user.memberships.filter(Q(organization__is_delivery_service=True,
                                                 organization__is_active=True,
                                                 organization__is_banned=False,
                                                 organization__is_deleted=False, ) &
                                               Q(
                                                   Q(role__can_deliver=True) |
                                                   Q(role__can_see_stats=True) |
                                                   Q(role__can_edit_organization=True)
                                               ))
        return bool(queryset.count())

    @classmethod
    def get_first_organization_of_user(cls, user: User):
        return Organization.objects.filter(memberships__user=user).first()

    @classmethod
    def get_user_role_in_organization(cls, organization: Organization, user: User) -> str:
        if organization.owner == user:
            return _('Owner')
        membership = MembershipService.get(organization=organization, user=user)
        return membership.role.title

    @classmethod
    def get_user_role_in_organization_or_client(cls, organization_id: int, user: User) -> str:
        organization = Organization.objects.get(id=organization_id)
        if organization.owner == user:
            return _('Owner')
        try:
            membership = MembershipService.get(organization=organization, user=user)
            return membership.role.title
        except:
            return _('Client')

    @classmethod
    def user_can_edit_organization(cls, organization: Organization, user: User) -> bool:
        permissions = cls.get_user_permissions_dict(organization=organization, user=user)
        return permissions['can_edit_organization']

    @classmethod
    def user_can_send_message(cls, organization_id: int, user: User) -> bool:
        organization = OrganizationService.get(id=organization_id)
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_send_message

    @classmethod
    def user_can_sell(cls, organization: Organization, user: User) -> bool:
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_sale

    @classmethod
    def user_can_see_stats(cls, organization: Organization, user: User) -> bool:
        permissions = cls.get_user_permissions_dict(organization=organization, user=user)
        return permissions['can_see_stats']

    @classmethod
    def user_can_check_attendance(cls, organization: Organization, user: User) -> bool:
        permissions = cls.get_user_permissions_dict(organization=organization, user=user)
        return permissions['can_check_attendance']

    @classmethod
    def user_can_edit_partner(cls, organization: Organization, user: User) -> bool:
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_edit_partner

    @classmethod
    def get_user_permissions_dict(cls, organization: Organization, user: User) -> dict:
        if organization.owner == user:
            permissions_dict = {
                'is_owner': True,
                'can_sale': True,
                'can_check_attendance': True,
                'can_see_stats': True,
                'can_edit_organization': True,
                'can_send_message': True,
                'can_edit_partner': True,
                'can_deliver': True if organization.is_delivery_service else False,
            }
            return permissions_dict

        try:
            role = MembershipService.get(organization=organization, user=user).role
            permissions_dict = {
                'is_owner': False,
                'can_sale': role.can_sale,
                'can_check_attendance': role.can_check_attendance,
                'can_see_stats': role.can_see_stats,
                'can_edit_organization': role.can_edit_organization,
                'can_send_message': role.can_send_message,
                'can_edit_partner': role.can_edit_partner,
                'can_deliver': role.can_deliver
            }
            return permissions_dict
        except ObjectNotFoundException:
            pass

        organization_ids_where_user_can_edit_partner = Membership.objects.filter(
            user=user, role__can_edit_partner=True).values_list('organization', flat=True).union(
            Organization.objects.filter(owner=user).values_list('id', flat=True))

        partner_organizations = Organization.objects.filter(
            id__in=organization_ids_where_user_can_edit_partner,
            requested_partnerships__is_accepted=True,
            requested_partnerships__accepted_by=organization
        ).distinct()

        can_check_attendance = False
        can_see_stats = False
        can_edit_organization = False

        for partner in partner_organizations:
            partnership = Partnership.objects.get(requested_by=partner, is_accepted=True, accepted_by=organization)
            if user == partner.owner:
                role_can_check_attendance = role_can_see_stats = role_can_edit_organization = True
            else:
                role = Role.objects.get(organization=partner, memberships__user=user)
                role_can_check_attendance = can_check_attendance or role.can_check_attendance
                role_can_see_stats = can_see_stats or role.can_see_stats
                role_can_edit_organization = can_edit_organization or role.can_edit_organization

            can_check_attendance = can_check_attendance or (
                    role_can_check_attendance and partnership.can_check_attendance)
            can_see_stats = can_see_stats or (role_can_see_stats and partnership.can_see_stats)
            can_edit_organization = can_edit_organization or (
                    role_can_edit_organization and partnership.can_edit_organization)

        return {
            'is_owner': False,
            'can_sale': False,
            'can_check_attendance': can_check_attendance,
            'can_see_stats': can_see_stats,
            'can_edit_organization': can_edit_organization,
            'can_send_message': False,
            'can_edit_partner': False,
            'can_deliver': False,
        }

    @classmethod
    def get_partners_dict(cls, organization: Organization) -> Tuple[int, QuerySet]:
        partners = cls.get_organization_partners(organization=organization)
        return partners.count(), partners[:3]

    @classmethod
    def get_organization_partners(cls, organization: Organization) -> QuerySet:
        return Organization.active_organizations.select_related('image').filter(
            id__in=organization.requested_partnerships.filter(is_accepted=True).values_list('accepted_by', flat=True))

    @classmethod
    def set_location(cls, organization, longitude, latitude, address):
        try:
            if longitude and latitude:
                point = Point(longitude, latitude)
            else:
                point = None
            organization.location = point
            organization.address = address
            organization.save()

            return organization

        except Exception:
            raise ValidationException(_('Something went wrong'))

    @classmethod
    @transaction.atomic
    def create_organization(cls, owner: User, title: str, image_id: File, longitude, latitude, numbers, accounts, cards,
                            avg_check=None, types=None, description=None, opens_at=None, closes_at=None,
                            address=None, country=None, currency=None, city=None):
        from organizations.services.card_services import DiscountCardService

        if not owner.is_staff and owner.owned_organizations.count() >= MAX_ORGANIZATIONS_PER_USER:
            raise BadRequestException(_(f'Can not create more than {MAX_ORGANIZATIONS_PER_USER} organizations'))

        country = country or Country.objects.get(code='KG')
        currency = currency or Currency.objects.get(code='KGS')

        if longitude and latitude:
            point = Point(longitude, latitude)
        else:
            point = None

        title_lang = GoogleTranslator().get_lang(title)
        if description:
            description_lang = GoogleTranslator().get_lang(description)
        else:
            description_lang = None

        organization = Organization.objects.create(owner=owner, title=title, title_lang=title_lang, opens_at=opens_at,
                                                   closes_at=closes_at, description_lang=description_lang,
                                                   description=description, image=image_id, address=address,
                                                   location=point, currency=currency, country=country, city=city,
                                                   avg_check=avg_check)
        if types is not None:
            organization.types.set(types)
        for number in numbers:
            OrgPhoneNumberService.create(organization=organization, number=number)
        for link in accounts:
            OrgSocialNetworkContactService.create(organization=organization, url=link)

        DiscountCardService.bulk_create_discounts(cards=cards, organization=organization)

        transaction.on_commit(lambda: send_notifications_to_all_users.delay(
            organization_id=organization.id,
            # sender_id=owner.id,
            mode=NOTIFICATION_MODE_SYSTEM,
            notification_type=NEW_ORGANIZATION,
            title=NEW_ORGANIZATION_TITLE,
            extra_data=dict(organization_title=organization.title)
        ))

        return organization

    @classmethod
    @transaction.atomic
    def update(cls, organization, image_id, longitude, latitude, types, title, opens_at, closes_at, address, currency,
               show_contacts, country, avg_check=None, description=None, city=None):
        try:
            if longitude and latitude:
                point = Point(longitude, latitude)
            else:
                point = None

            title_lang = GoogleTranslator().get_lang(title)
            if description:
                description_lang = GoogleTranslator().get_lang(description)
            else:
                description_lang = None

            organization.title_lang = title_lang
            organization.description_lang = description_lang
            organization.image_id = image_id
            organization.location = point
            organization.title = title
            organization.opens_at = opens_at
            organization.closes_at = closes_at
            organization.address = address
            organization.avg_check = avg_check
            if not organization.currency == currency:
                from organizations.services.partnership_services import PartnershipService
                if not PartnershipService.can_change_currency(organization=organization, currency=currency):
                    raise NotAcceptableException(_('Can not update currency. It is different from partners'))

                from organizations.services.card_services import DiscountCardService
                DiscountCardService.update_discount_currency(organization=organization, new_currency=currency.code)
            organization.currency = currency
            organization.show_contacts = show_contacts
            organization.country = country
            organization.city = city
            organization.description = description
            organization.types.set(types)
            organization.save()

            return organization

        except Exception as e:
            raise IntegrityException(_('Could not update organization: {e}').format(e=str(e)))

    @classmethod
    def deactivate(cls, organization: Organization):
        try:
            organization.is_deleted = True
            organization.save()
            from shop.services.cart_services import CartService
            CartService.delete_organization_carts(organization=organization)
            return organization
        except Exception as e:
            raise IntegrityException(_('Could not deactivate organization: {e}').format(e=str(e)))

    @classmethod
    def reactivate(cls, organization: Organization) -> Organization:
        try:
            organization.is_deleted = False
            organization.save()
            return organization
        except Exception as e:
            raise IntegrityException(_('Could not reactivate organization: {e}').format(e=str(e)))

    @classmethod
    def reset_running_purchase_id(cls, organization: Organization) -> Organization:
        try:
            organization.running_purchase_id = 1
            organization.save()
            return organization
        except Exception as e:
            raise IntegrityException(_('Could not reset running purchase ID organization: {e}').format(e=str(e)))

    @classmethod
    def increment_running_purchase_id(cls, organization: Organization):
        organization.running_purchase_id = F('running_purchase_id') + 1
        organization.save()
        organization.refresh_from_db()

    @classmethod
    def get_organizations_ordered_by_num_of_partners(cls,
                                                     country: Union[Country, None] = None,
                                                     city: Union[City, None] = None) -> QuerySet:
        queryset = Organization.objects.filter(requested_partnerships__is_accepted=True)
        queryset = cls._filter_by_country_and_city(queryset=queryset, country=country, city=city)

        queryset = queryset.annotate(
            partners_count=Coalesce(Count('requested_partnerships'), 0)).exclude(
            partners_count__lt=HOMEPAGE_MIN_ORDERED_PARTNERS_THRESHOLD).order_by('-partners_count')
        return queryset

    @classmethod
    def get_random_organizations_with_min_count_of_partners(cls, min_count: int = HOMEPAGE_MIN_PARTNERS_THRESHOLD,
                                                            country: Union[Country, None] = None,
                                                            city: Union[City, None] = None) -> QuerySet:
        queryset = Organization.objects.select_related('image').filter(requested_partnerships__is_accepted=True)
        queryset = cls._filter_by_country_and_city(queryset=queryset, country=country, city=city)

        queryset = queryset.annotate(
            partners_count=Coalesce(Count('requested_partnerships'), 0)
        ).exclude(partners_count__lt=min_count)[:HOMEPAGE_PARTNERS_COUNT]

        # This is fucking shit, but i comment it
        # q_list = list(queryset)
        # random.shuffle(q_list)
        return queryset

    @classmethod
    def get_random_organizations_with_discounts(cls, limit: int = HOMEPAGE_BANNERS_COUNT,
                                                country: Union[Country, None] = None,
                                                city: Union[City, None] = None) -> list:
        queryset = Organization.active_organizations.exclude(discounts__isnull=True)
        queryset = cls._filter_by_country_and_city(queryset=queryset, country=country, city=city)

        queryset = queryset.order_by('?')[:limit]
        return queryset

    @classmethod
    def _filter_by_country_and_city(cls, queryset: QuerySet,
                                    country: Union[Country, None] = None, city: Union[City, None] = None) -> QuerySet:
        if country is not None:
            queryset = queryset.filter(country=country)
        if city is not None:
            queryset = queryset.filter(city=city)
        return queryset

    @classmethod
    def get_random_organizations_in_category(cls, category: OrganizationCategory,
                                             partner: Organization = None,
                                             country: Union[Country, None] = None,
                                             city: Union[City, None] = None) -> QuerySet:
        additional = Organization.active_organizations.filter(is_active=True, types__in=category.types.all()).distinct()
        queryset = Organization.active_organizations.prefetch_related('types').select_related('image').filter(
            id__in=additional).order_by('?')

        if partner is not None:
            queryset = queryset.filter(id__in=cls.get_organization_partners(partner))
        queryset = cls._filter_by_country_and_city(queryset=queryset, country=country, city=city)

        return queryset

    @classmethod
    def get_organizations_in_category(cls, category: OrganizationCategory,
                                      partner: Organization = None,
                                      country: Union[Country, None] = None,
                                      city: Union[City, None] = None) -> QuerySet:
        queryset = Organization.objects.filter(is_active=True, types__in=category.types.all()).distinct().annotate(
            cards_count=Count(
                'discounts', distinct=True, filter=Q(discounts__is_published=True))
        ).order_by('-cards_count')

        if partner is not None:
            queryset = queryset.filter(id__in=cls.get_organization_partners(partner))

        queryset = cls._filter_by_country_and_city(queryset=queryset, country=country, city=city)

        return queryset

    @classmethod
    def get_organizations_in_service(cls, request, service: Service, country: Union[Country, None] = None,
                                     city: Union[City, None] = None) -> QuerySet:

        timestamp = request.META.get('HTTP_DEVICE_TIMESTAMP', timezone.now().strftime("%Y-%m-%dT%H:%M:%S"))
        locale_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")

        queryset = Organization.objects.filter(is_active=True, has_delivery=True, types__in=service.subcategory.all(),
                                               shop_items__isnull=False, shop_items__price__isnull=False
                                               ).exclude(is_banned=True).exclude(is_deleted=True).distinct()

        queryset = cls._filter_by_country_and_city(queryset=queryset, country=country, city=city)

        try:
            queryset = queryset.annotate(time_now=ExpressionWrapper(Value(locale_time.time()),
                                                                    output_field=TimeField()))
        except AttributeError:
            raise NotAcceptableException(
                _('Valid time are required in headers'))

        queryset = queryset.annotate(time_working=Case(
            When(opens_at=F('closes_at'), then=1),
            When(opens_at__lte=F('time_now'), closes_at__gte=F('time_now'), then=2),
            When(opens_at__gte=F('closes_at'), time_now__gte=F('opens_at'),
                 time_now__range=([F('opens_at'), '23:59:59']), then=2),
            When(opens_at__gte=F('closes_at'), time_now__lte=F('closes_at'),
                 time_now__range=(['00:00:00', F('closes_at')]), then=2),
            default=Value(3),
            output_field=IntegerField(),
        )).order_by('time_working')

        # print(locale_time)
        # for i in queryset:
        #     print(i.id, i.time_now, i.opens_at, i.closes_at, i.time_working)

        return queryset

    @classmethod
    def get_working_time_status(cls, queryset, request):
        timestamp = request.META.get('HTTP_DEVICE_TIMESTAMP', timezone.now().strftime("%Y-%m-%dT%H:%M:%S"))
        locale_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")



        queryset = queryset.annotate(time_now=ExpressionWrapper(Value(locale_time.time()), output_field=TimeField()))

        queryset = queryset.annotate(time_working=Case(
            When(opens_at=F('closes_at'), then=Value("around_the_clock")),
            When(opens_at__lte=F('time_now'), closes_at__gte=F('time_now'), then=Value("open")),
            When(opens_at__gte=F('closes_at'), time_now__gte=F('opens_at'),
                 time_now__range=([F('opens_at'), '23:59:59']), then=Value("open")),
            When(opens_at__gte=F('closes_at'), time_now__lte=F('closes_at'),
                 time_now__range=(['00:00:00', F('closes_at')]), then=Value("open")),
            default=Value("closed"),
            output_field=CharField(),
        ))

        # print(locale_time)
        # for i in queryset:
        #     print(i.id, i.title, i.time_now, i.opens_at, i.closes_at, i.time_working)

        return queryset

    @classmethod
    def change_organization_owner(cls, organization: Organization, new_owner: User, current_owner: User):
        if not organization.owner == current_owner:
            raise PermissionDeniedException(_('No rights to change owner'))
        try:
            organization.owner = new_owner
            organization.save()

            sent_notification.delay(
                recipient_id=new_owner.id,
                sender_id=current_owner.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=ORGANIZATION_OWN_TYPE,
                organization_id=organization.id,
                extra_data=dict(organization=organization.title)
            )

            sent_notification.delay(
                recipient_id=current_owner.id,
                sender_id=new_owner.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=ORGANIZATION_GAVE_TYPE,
                description=ORGANIZATION_GAVE_DESCRIPTION,
                organization_id=organization.id,
                extra_data=dict(organization=organization.title)
            )

        except IntegrityError:
            raise IntegrityException(_('Could not change owner'))

    @classmethod
    def get_online_client(cls, user_id: int, organization_id: int, requested_by: User) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        user = User.objects.get(id=user_id)
        if not MembershipService.is_organization_member_or_owner(user=requested_by, organization=organization):
            raise PermissionDeniedException(_('Permission denied'))

        if Transaction.objects.filter(client=user, organization=organization, type=Transaction.ONLINE).exists():
            return user

        raise ObjectNotFoundException(_('Client not found'))


class OrgPhoneNumberService:
    model = PhoneNumber

    @classmethod
    def create(cls, organization: Organization, number: str) -> PhoneNumber:
        return PhoneNumber.objects.create(organization=organization, phone_number=number)

    @classmethod
    def get_numbers_of_organization(cls, organization_id: int) -> QuerySet:
        return PhoneNumber.objects.filter(organization_id=organization_id)

    @classmethod
    def update_phone_numbers(cls, organization_id: int, user: User, numbers: list):
        organization = OrganizationService.get(id=organization_id)
        if not OrganizationService.user_can_edit_organization(organization=organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        with transaction.atomic():
            PhoneNumber.objects.filter(organization_id=organization_id).delete()
            numbers = [PhoneNumber(organization_id=organization_id, phone_number=number) for number in numbers]
            PhoneNumber.objects.bulk_create(numbers)
            return numbers


class OrgSocialNetworkContactService:
    model = SocialNetworkContact

    @classmethod
    def create(cls, organization: Organization, url: str) -> PhoneNumber:
        return SocialNetworkContact.objects.create(organization=organization, url=url)

    @classmethod
    def get_networks_of_organization(cls, organization_id: int) -> QuerySet:
        return SocialNetworkContact.objects.filter(organization_id=organization_id)

    @classmethod
    def update_social_networks(cls, organization_id: int, user: User, urls: list):
        organization = OrganizationService.get(id=organization_id)
        if not OrganizationService.user_can_edit_organization(organization=organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        with transaction.atomic():
            SocialNetworkContact.objects.filter(organization_id=organization_id).delete()
            contacts = [SocialNetworkContact(organization_id=organization_id, url=url) for url in urls]
            SocialNetworkContact.objects.bulk_create(contacts)
            return contacts


class OrganizationInstagramIntegrationService:
    model = InstagramIntegration

    @classmethod
    def check_instagram_account(cls, url: str) -> dict:
        try:
            username = get_username_from_instagram_url(url)
            user_info = get_instagram_user_info(username)
            return user_info
        except:
            raise ObjectNotFoundException(_('Instagram user not found'))

    @classmethod
    def create(cls, organization: Organization, url: str) -> InstagramIntegration:
        try:
            username = get_username_from_instagram_url(url)
            user_info = get_instagram_user_info(username)

            avatar = File.objects.create(image_url=user_info.get('profile_image'))
            instance = InstagramIntegration.objects.create(organization=organization,
                                                           url=url,
                                                           account_user_name=username,
                                                           account_user_id=user_info.get('user_id'),
                                                           account_full_name=user_info.get('full_name'),
                                                           avatar=avatar)
            parse_instagram_to_shop_items.delay(organization_id=organization.id)
            return instance
        except Exception as e:
            raise BadRequestException(_('Instagram user not found : {e}').format(e=str(e)))

    @classmethod
    def delete(cls, organization: Organization):
        try:
            insta = InstagramIntegration.objects.get(organization=organization)
            insta.delete()
            transaction.on_commit(
                lambda: delete_not_updated_posts_from_instagram.delay(organization_id=organization.id))
        except:
            raise ObjectNotFoundException(_('Instagram Integration Link not found'))

    @classmethod
    def get_from_org(cls, organization: Organization):
        try:
            return InstagramIntegration.objects.get(organization=organization)

        except:
            raise ObjectNotFoundException(_('Instagram Integration Link not found'))


class OrgMessageService:
    model = Message

    @classmethod
    def get_messages_of_organization(cls, organization_id: int) -> QuerySet:
        return cls.model.objects.filter(organization_id=organization_id)

    @classmethod
    def get_messages_of_subscriptions(cls, user: User) -> QuerySet:
        organizations = Subscription.objects.filter(user=user).values('organization')
        return cls.model.objects.filter(organization__in=organizations)

    @classmethod
    def get_received_messages(cls, user: User) -> QuerySet:
        return Message.objects.filter(receivers=user)

    @classmethod
    def send_message(cls, organization: Organization, content: str, sender: User, message_to: str):
        receivers = ()
        notification_sender_id = None
        partners_to_save = ()
        partners = OrganizationService.get_organization_partners(organization=organization).distinct().values('id', )
        if message_to == "organization_followers":
            receivers = User.objects.filter(subscriptions__organization_id=organization.id).distinct()
        elif message_to == "partners_followers":
            notification_sender_id = sender.id
            partners_to_save = OrganizationService.get_organization_partners(organization=organization).distinct()
            receivers = User.objects.filter(subscriptions__organization_id__in=partners).distinct()
        elif message_to == "partners_members":
            notification_sender_id = sender.id
            partners_to_save = OrganizationService.get_organization_partners(organization=organization).distinct()
            receivers = User.objects.filter(
                Q(memberships__organization_id__in=partners) | Q(owned_organizations__in=partners)).distinct()

        message = cls.model.objects.create(organization=organization, content=content, sender=sender,
                                           message_to=message_to)
        message.receivers.set(receivers)
        message.receiver_partners.set(partners_to_save)

        for receiver in receivers:
            sent_notification.delay(
                sender_id=notification_sender_id,
                organization_id=organization.id,
                recipient_id=receiver.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=ORGANIZATION_MESSAGE_TYPE,
                extra_data=dict(message_to=message_to, content=content)
            )
        send_notifications_organization_members.delay(
            sender_id=sender.id,
            mode=NOTIFICATION_MODE_PERSONAL,
            notification_type=ORGANIZATION_MESSAGE_SENDER_TYPE,
            organization_id=organization.id,
            with_permissions=dict(can_send_message=True),
            members_organization_id=organization.id,
            extra_data=dict(can_send_message=True, message_to=message_to, content=content)
        )
        return message
