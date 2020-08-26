import random
from typing import Tuple

from django.contrib.gis.geos import Point
from django.db import transaction, IntegrityError
from django.db.models import QuerySet, Count, Q
from django.db.models.functions import Coalesce

from common.exceptions import (
    ObjectNotFoundException, ValidationException, IntegrityException,
    NotAcceptableException, PermissionDeniedException
)
from notifications.constants import (SYSTEM_NOTIFICATION_MODE, NEW_ORGANIZATION, NEW_ORGANIZATION_TITLE,
                                     NEW_ORGANIZATION_DESCRIPTION, ORGANIZATION_MESSAGE_TYPE, PERSONAL_MODE,
                                     ORGANIZATION_MESSAGE_TITLE, ORGANIZATION_MESSAGE_DESCRIPTION,
                                     ORGANIZATION_OWNER_MESSAGE_TITLE, ORGANIZATION_OWN_TYPE, ORGANIZATION_OWN_TITLE,
                                     ORGANIZATION_OWN_DESCRIPTION, ORGANIZATION_GAVE_TYPE, ORGANIZATION_GAVE_TITLE,
                                     ORGANIZATION_GAVE_DESCRIPTION, ORGANIZATION_MESSAGE_SENDER_TYPE)
from notifications.tasks import (
    send_notifications_to_all_users, sent_notification,
    send_notifications_organization_members
)
from organizations.constants import HOMEPAGE_BANNERS_COUNT, HOMEPAGE_MIN_PARTNERS_THRESHOLD, HOMEPAGE_PARTNERS_COUNT
from organizations.models import (
    Organization, OrganizationCategory, PhoneNumber, SocialNetworkContact, Message, Subscription
)
from organizations.services.membership_services import MembershipService
from users.models import User


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
            raise ObjectNotFoundException('Organization not found')

    @classmethod
    def get_user_role_in_organization(cls, organization: Organization, user: User) -> str:
        if organization.owner == user:
            return 'Собственник'
        membership = MembershipService.get(organization=organization, user=user)
        return membership.role.title

    @classmethod
    def user_can_edit_organization(cls, organization: Organization, user: User) -> bool:
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_edit_organization

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
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_see_stats

    @classmethod
    def user_can_check_attendance(cls, organization: Organization, user: User) -> bool:
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_check_attendance

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
            return {
                'is_owner': True,
                'can_sale': True,
                'can_check_attendance': True,
                'can_see_stats': True,
                'can_edit_organization': True,
                'can_send_message': True,
                'can_edit_partner': True
            }

        try:
            role = MembershipService.get(organization=organization, user=user).role
            return {
                'is_owner': False,
                'can_sale': role.can_sale,
                'can_check_attendance': role.can_check_attendance,
                'can_see_stats': role.can_see_stats,
                'can_edit_organization': role.can_edit_organization,
                'can_send_message': role.can_send_message,
                'can_edit_partner': role.can_edit_partner
            }
        except ObjectNotFoundException:
            return {
                'is_owner': False,
                'can_sale': False,
                'can_check_attendance': False,
                'can_see_stats': False,
                'can_edit_organization': False,
                'can_send_message': False,
                'can_edit_partner': False
            }

    @classmethod
    def get_partners_dict(cls, organization: Organization) -> Tuple[int, QuerySet]:
        partners = cls.get_organization_partners(organization=organization)
        return partners.count(), partners[:3]

    @classmethod
    def get_organization_partners(cls, organization: Organization) -> QuerySet:
        return Organization.objects.filter(
            id__in=organization.requested_partnerships.filter(is_accepted=True).values_list('accepted_by', flat=True))

    @classmethod
    def set_location(cls, organization, longitude, latitude, address):
        try:
            point = Point(longitude, latitude)
            organization.location = point
            organization.address = address
            organization.save()

            return organization

        except Exception:
            raise ValidationException('Something went wrong')

    @classmethod
    @transaction.atomic
    def create_organization(cls, owner, title, description, image_id,
                            opens_at, closes_at, address, longitude, latitude,
                            types, numbers, accounts, cards, currency="KGS", country="KG"):
        from organizations.services.card_services import DiscountCardService

        point = Point(longitude, latitude)
        organization = Organization.objects.create(owner=owner, title=title, opens_at=opens_at, closes_at=closes_at,
                                                   description=description, image_id=image_id, address=address,
                                                   location=point, currency=currency, country=country)
        organization.types.set(types)
        for number in numbers:
            OrgPhoneNumberService.create(organization=organization, number=number)
        for link in accounts:
            OrgSocialNetworkContactService.create(organization=organization, url=link)

        DiscountCardService.bulk_create_discounts(cards=cards, organization=organization)

        transaction.on_commit(lambda: send_notifications_to_all_users.delay(
            organization_id=organization.id,
            # sender_id=owner.id,
            mode=SYSTEM_NOTIFICATION_MODE,
            notification_type=NEW_ORGANIZATION,
            title=NEW_ORGANIZATION_TITLE,
            description=NEW_ORGANIZATION_DESCRIPTION.format(organization_title=organization.title)
        ))

        return organization

    @classmethod
    @transaction.atomic
    def update(cls, organization, image_id, longitude, latitude, description, types,
               title, opens_at, closes_at, address, currency, show_contacts, country):
        try:
            point = Point(longitude, latitude)
            organization.image_id = image_id
            organization.location = point
            organization.title = title
            organization.opens_at = opens_at
            organization.closes_at = closes_at
            organization.address = address
            if not organization.currency == currency:
                from organizations.services.card_services import DiscountCardService
                DiscountCardService.update_discount_currency(organization=organization, new_currency=currency.code)

            organization.currency = currency
            organization.show_contacts = show_contacts
            organization.country = country
            organization.description = description
            organization.types.set(types)
            organization.save()

            return organization

        except Exception as e:
            raise IntegrityException('Can not update organization: {e}'.format(e=str(e)))

    @classmethod
    def deactivate(cls, organization):
        try:
            organization.is_deleted = True
            organization.save()

            return organization

        except Exception as e:
            raise IntegrityException('Can not deactivate organization: {e}'.format(e=str(e)))

    @classmethod
    def get_organizations_ordered_by_num_of_partners(cls) -> QuerySet:
        queryset = Organization.objects.filter(requested_partnerships__is_accepted=True).annotate(
            partners_count=Coalesce(Count('requested_partnerships'), 0)).order_by('-partners_count')
        return queryset

    @classmethod
    def get_random_organizations_with_min_count_of_partners(
            cls, min_count: int = HOMEPAGE_MIN_PARTNERS_THRESHOLD) -> list:
        queryset = Organization.objects.filter(requested_partnerships__is_accepted=True).annotate(
            partners_count=Coalesce(Count('requested_partnerships'), 0)
        ).exclude(partners_count__lt=min_count)[:HOMEPAGE_PARTNERS_COUNT]

        q_list = list(queryset)
        random.shuffle(q_list)
        return q_list

    @classmethod
    def get_random_organizations_with_discounts(cls, limit: int = HOMEPAGE_BANNERS_COUNT) -> list:
        queryset = Organization.objects.exclude(discounts__isnull=True).order_by('?')[:limit]
        return queryset

    @classmethod
    def get_organizations_in_category_with_search(cls, category: OrganizationCategory, partner: Organization = None,
                                                  search=None) -> QuerySet:
        queryset = Organization.objects.filter(is_active=True, types__in=category.types.all(),
                                               title__icontains=search).distinct().annotate(
            cards_count=Count(
                'discounts', distinct=True, filter=Q(discounts__is_published=True))).order_by('-cards_count')
        if partner is not None:
            queryset = queryset.filter(id__in=cls.get_organization_partners(partner))
        return queryset

    @classmethod
    def get_random_organizations_in_category(cls, category: OrganizationCategory,
                                             partner: Organization = None) -> QuerySet:
        additional = Organization.objects.filter(is_active=True, types__in=category.types.all()).distinct()
        queryset = Organization.objects.filter(id__in=additional).order_by('?')

        if partner is not None:
            queryset = queryset.filter(id__in=cls.get_organization_partners(partner))

        return queryset

    @classmethod
    def get_organizations_in_category(cls, category: OrganizationCategory, partner: Organization = None) -> QuerySet:
        queryset = Organization.objects.filter(is_active=True, types__in=category.types.all()).distinct().annotate(
            cards_count=Count(
                'discounts', distinct=True, filter=Q(discounts__is_published=True))
        ).order_by('-cards_count')

        if partner is not None:
            queryset = queryset.filter(id__in=cls.get_organization_partners(partner))

        return queryset

    @classmethod
    def change_organization_owner(cls, organization: Organization, new_owner: User, current_owner: User):
        if not organization.owner == current_owner:
            raise PermissionDeniedException('No rights to change owner')
        try:
            organization.owner = new_owner
            organization.save()

            sent_notification.delay(
                recipient_id=new_owner.id,
                sender_id=current_owner.id,
                mode=PERSONAL_MODE,
                notification_type=ORGANIZATION_OWN_TYPE,
                title=ORGANIZATION_OWN_TITLE.format(organization=organization.title),
                description=ORGANIZATION_OWN_DESCRIPTION,
                organization_id=organization.id
            )

            sent_notification.delay(
                recipient_id=current_owner.id,
                sender_id=new_owner.id,
                mode=PERSONAL_MODE,
                notification_type=ORGANIZATION_GAVE_TYPE,
                title=ORGANIZATION_GAVE_TITLE.format(organization=organization.title),
                description=ORGANIZATION_GAVE_DESCRIPTION,
                organization_id=organization.id
            )

        except IntegrityError:
            raise IntegrityException('Could not change owner')


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
            raise NotAcceptableException('No rights to edit organization')

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
            raise NotAcceptableException('No rights to edit organization')

        with transaction.atomic():
            SocialNetworkContact.objects.filter(organization_id=organization_id).delete()
            contacts = [SocialNetworkContact(organization_id=organization_id, url=url) for url in urls]
            SocialNetworkContact.objects.bulk_create(contacts)
            return contacts


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
        receivers = None
        partners = OrganizationService.get_organization_partners(organization=organization).distinct().values('id', )
        if message_to == "organization_followers":
            receivers = User.objects.filter(subscriptions__organization_id=organization.id).distinct()
        elif message_to == "partners_followers":
            receivers = User.objects.filter(subscriptions__organization_id__in=partners).distinct()
        elif message_to == "partners_members":
            receivers = User.objects.filter(
                Q(memberships__organization_id__in=partners) | Q(owned_organizations__in=partners)).distinct()

        partners_to_save = OrganizationService.get_organization_partners(organization=organization).distinct()

        message = cls.model.objects.create(organization=organization, content=content, sender=sender,
                                           message_to=message_to)
        message.receivers.set(receivers)
        message.receiver_partners.set(partners_to_save)

        for receiver in receivers:
            sent_notification.delay(
                organization_id=organization.id,
                recipient_id=receiver.id,
                mode=PERSONAL_MODE,
                notification_type=ORGANIZATION_MESSAGE_TYPE,
                title=ORGANIZATION_MESSAGE_TITLE.format(organization=organization.title),
                description=ORGANIZATION_MESSAGE_DESCRIPTION.format(content=content)
            )
        send_notifications_organization_members.delay(
            sender_id=sender.id,
            mode=PERSONAL_MODE,
            notification_type=ORGANIZATION_MESSAGE_SENDER_TYPE,
            title=ORGANIZATION_OWNER_MESSAGE_TITLE,
            description=ORGANIZATION_MESSAGE_DESCRIPTION.format(content=content),
            organization_id=organization.id,
            with_permissions=dict(can_send_message=True),
            members_organization_id=organization.id,
            extra_data=dict(can_send_message=True)
        )
        return message
