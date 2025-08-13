import datetime
import random

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, IntegerField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    GenericAPIView,
    UpdateAPIView,
    CreateAPIView,
    DestroyAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import (
    NotAcceptableException,
    ObjectNotFoundException,
    IntegrityException,
)
from common.utils import method_permission_classes
from common.services import slack
from instagram_parsers.services.proxy_services import ProxyService
from mailer.services import MailerService
from organizations.constants import UNDER_REVIEW, TEST
from organizations.models import (
    Organization,
    OrganizationCategory,
    OrganizationType,
    InstagramIntegration,
    Service,
    OrganizationComplaint,
    OrganizationBlacklist,
    BlockedUser,
    Subscription,
    UserAssistant,
    RegionalTariff,
    PaymentSystemMethod,
    OrganizationBanner,
)
from organizations.permissions import IsAnyOrganizationOwnerOrAdmin
from organizations.serializers.categories_serializers import (
    OrganizationCategorySerializer,
    HomepageOrganizationsSerializer,
    OrganizationWithDiscountsSerializer,
    OrganizationTypeSerializer,
)

from organizations.serializers.misc_serializers import LocationSerializer
from organizations.serializers.organization_serializers import (
    OrganizationListSerializer,
    OrganizationCreateSerializer,
    OrganizationDetailedSerializer,
    OrganizationUpdateSerializer,
    OrgPhoneNumberSerializer,
    OrgPhoneNumberEditSerializer,
    OrgSocialNetworkContactSerializer,
    OrgSocialNetworkEditSerializer,
    OrganizationSerializer,
    OrgMessageSerializer,
    OrgMessageCreateSerializer,
    SubscriptionsMessageSerializer,
    OrganizationWithImageSerializer,
    InstagramIntegrationCreateUpdateSerializer,
    InstagramIntegrationLinkSerializer,
    DeliverySettingsUpdateSerializer,
    OrganizationTitleSerializer,
    OrgVerificationsSerializer,
    OrganizationComplaintSerializer,
    OrganizationBlacklistSerializer,
    BlockedUserSerializer,
    OrganizationGoogleMapsCreateSerializer,
    OrganizationTwoGisCreateSerializer,
    PaymentSystemSerializer,
    OrgPaymentSystemConfirmationSerializer,
    OrganizationMapsListSerializer,
    OrganizationNameListSerializer,
    RegionalTariffSerializer,
    PurchaseOrgSubscriptionSerializer,
    OrganizationBannerSerializer,
    OrganizationBannerCreateSerializer,
)
from organizations.serializers.query_param_serializers import (
    PartnerQueryParamSerializer,
    OrganizationAndCategorySerializer,
    OrganizationCoutrySerializer,
    OrganizationMapsLocationSerializer,
    OrganizationQueryParamSerializer,
    OrganizationNumSubsQueryParamSerializer,
    CountryQueryParamSerializer,
)
from organizations.serializers.service_serializers import (
    ItemServiceSerializer,
    OrganizationServiceSerializer,
)
from organizations.services.categories_services import OrganizationCategoryService
from organizations.services.google_maps_services import GoogleMapsService, TwoGisService
from organizations.services.organization_services import (
    ItemService,
    OrganizationService,
    OrgPhoneNumberService,
    OrgSocialNetworkContactService,
    OrgMessageService,
    OrganizationInstagramIntegrationService,
    OrganizationBannerService,
)
from organizations.services.subscription_services import (
    SubscriptionService,
    UserOrgSubscriptionService,
)
from organizations.services.verifications_service import (
    VerificationService,
    PaymentSystemConfirmationService,
)
from organizations.tasks import (
    parse_instagram_to_shop_items,
    add_subscribers_to_organization,
)
from shop.filters import FeedItemFilter, FeedItemOrderingFilter
from shop.models import ShopItem
from shop.serializers.item_serializers import ItemFeedSerializer
from shop.services.comment_services import CommentService
from shop.services.item_services import ShopItemService
from users.serializers import UserShortInfoSerializer, FollowerOrClientSerializer
from users.services import UserService

User = get_user_model()


class OrgVerifications(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrgVerificationsSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        serializer = OrgVerificationsSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        VerificationService.create(organization, **serializer.validated_data)

        apofiz_email = settings.EMAIL_HOST_USER
        MailerService.send_verifications_email(
            email=apofiz_email, org_id=organization.pk, send_time=timezone.now()
        )

        organization.verification_status = UNDER_REVIEW
        organization.save(update_fields=("verification_status",))

        return Response(
            {"message": "verifications data successfully created"},
            status=status.HTTP_201_CREATED,
        )


class OrgPaymentSystemConfirmation(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrgPaymentSystemConfirmationSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        serializer = OrgPaymentSystemConfirmationSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        payment_system_id = serializer.validated_data.get("payment_system_id", None)
        if payment_system_id == 1:
            payment_system_name = "FreedomPay"
        elif payment_system_id == 2:
            payment_system_name = "PaySy"
        elif payment_system_id == 3:
            payment_system_name = "Crypto Box"
        else:
            raise NotAcceptableException(_("Unknown Payment System"))

        PaymentSystemConfirmationService.create(
            organization, **serializer.validated_data
        )

        apofiz_email = settings.EMAIL_HOST_USER
        MailerService.send_payment_verification_email(
            email=apofiz_email,
            org_id=organization.pk,
            send_time=timezone.now(),
            payment_system_name=payment_system_name,
        )

        return Response(
            {"message": "Payment system data successfully created"},
            status=status.HTTP_201_CREATED,
        )


class OrgWholesaleConfirmation(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        if not organization.can_update_is_wholesale:
            apofiz_email = settings.EMAIL_HOST_USER
            MailerService.send_wholesale_verification_email(
                email=apofiz_email, org_id=organization.pk, send_time=timezone.now()
            )
            slack_message = (
                f"Organization\n"
                f"https://apofiz.com/971585333939admin/organizations/organization/{organization.pk}/change/\n"
                f"sent a connection request to the wholesale organization.\n"
                f"============================"
            )
            slack.bot(slack_message)
            organization.is_wholesale_request_timestamp = timezone.now()
            organization.save()

            return Response(
                {"message": "Request successfully sent"}, status=status.HTTP_200_OK
            )

        return Response(
            {"message": "You can already update the is_wholesale field"},
            status=status.HTTP_200_OK,
        )


class OrganizationCreationLimitView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = {
            "can_add_organization": not OrganizationService.creation_limit_exceeded(
                user=request.user
            ),
            "is_delivery_service": OrganizationService.is_delivery_service(
                user=request.user
            ),
        }
        return Response(data=data)


class OrganizationsListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Organization.objects.filter(Q(owner=user) | Q(memberships__user=user))
            .annotate(
                priority=Case(
                    When(owner=user, then=0),
                    default=1,
                    output_field=IntegerField(),
                )
            )
            .order_by("priority")
            .distinct()
        )

    def create(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = OrganizationService.create_organization(
            **serializer.validated_data
        )

        num_members = random.randint(28, 130)
        if organization.country.code == "AE":
            transaction.on_commit(
                lambda: add_subscribers_to_organization.delay(
                    organization.id, num_members
                )
            )

        data = OrganizationDetailedSerializer(
            organization, context={"request": request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationMakeSubsCreateView(CreateAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrganizationNumSubsQueryParamSerializer(data=request.data)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _("Valid organization is required in query parameters")
            )

        organization = serializer.validated_data["organization"]
        number_of_subs = serializer.validated_data["number_of_subs"]

        transaction.on_commit(
            lambda: add_subscribers_to_organization.delay(
                organization.id, number_of_subs
            )
        )

        return Response({"message": "Success"}, status=status.HTTP_200_OK)


class MyOrganizationsWithCanEditListCreateView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(
            Q(owner=user, is_deleted=False)
            | Q(
                memberships__user=user,
                is_deleted=False,
                memberships__role__can_edit_organization=True,
            )
        ).distinct()


class MyOrganizationsListCreateView(ListAPIView):
    serializer_class = OrganizationNameListSerializer
    pagination_class = None

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id", None)
        user = UserService.get(id=int(user_id))
        return Organization.objects.filter(
            Q(owner=user, is_deleted=False)
            | Q(
                memberships__user=user,
                is_deleted=False,
                memberships__role__can_edit_organization=True,
            )
        ).distinct()


class OrganizationsMapsListView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationMapsListSerializer

    def get(self, request, *args, **kwargs):
        serializer = OrganizationMapsLocationSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        search_query = request.GET.get("search")
        data = OrganizationService.get_organizations_by_location_for_map(
            type=serializer.validated_data["type"], search=search_query
        )

        return Response(data)


class OrganizationsMapsCountryCityListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationMapsListSerializer
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        country = serializer.validated_data["country"]
        city = serializer.validated_data["city"]
        type = serializer.validated_data["type"]

        return OrganizationService.get_organizations_by_country_city_for_map(
            country=country, city=city, type=type
        )


# class OrganizationsGoogleMapsCreateView(CreateAPIView):
#     permission_classes = (IsAuthenticated,)
#     serializer_class = OrganizationGoogleMapsCreateSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#
#         if not serializer.is_valid():
#             return Response(data={
#                 'message': _('Invalid input'),
#                 'errors': serializer.errors
#             }, status=status.HTTP_406_NOT_ACCEPTABLE)
#         google_maps_url = serializer.validated_data['google_maps_url']
#         parsed_data = GoogleMapsService.add_organization(google_maps_url, request)
#         return Response(parsed_data)


class OrganizationsGoogleMapsCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationGoogleMapsCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        google_maps_url = serializer.validated_data["google_maps_url"]

        remote_service_url = "http://161.35.153.151:8080/bot/google-maps/"

        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        try:
            response = requests.post(
                remote_service_url,
                json={
                    "google_maps_url": google_maps_url,
                    "proxy": proxy[0],
                    "host": request.META.get("HTTP_HOST", "test.apofiz.com"),
                },
                headers={"Authorization": request.headers.get("Authorization")},
            )

            if response.status_code != 200:
                return Response(data=response.json(), status=response.status_code)

            return Response(response.json())

        except requests.RequestException as e:
            return Response(
                data={
                    "message": _("Error connecting to Google Maps service"),
                    "errors": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class OrganizationsTwoGisCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationTwoGisCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        two_gis_url = serializer.validated_data["two_gis_url"]
        parsed_data = TwoGisService.add_organization(two_gis_url, request)
        return Response(parsed_data)


class OrganizationTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = OrganizationCategorySerializer
    queryset = OrganizationCategory.objects.all().exclude(types__is_resume=True)


class OrganizationAllTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    serializer_class = OrganizationTypeSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ["category"]
    search_fields = ["title"]
    queryset = OrganizationType.objects.all().exclude(is_resume=True)


class OrganizationMapsTypesListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationTypeSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ["category"]
    search_fields = ["title"]

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)

        return OrganizationService.get_organization_types_by_country(
            country=serializer.validated_data["country"]
        )


class OrganizationRetrieveUpdateView(RetrieveAPIView):
    serializer_class = OrganizationDetailedSerializer
    queryset = Organization.objects.all()

    def get_queryset(self):
        queryset = OrganizationService.get_working_time_status(
            self.queryset, self.request
        )
        return queryset

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        context = {
            "request": request,
        }

        if (
            datetime.datetime.now() - instance.add_item_date.replace(tzinfo=None)
        ).days > 6 and instance.owner == request.user:
            OrganizationService.update_add_item_date(
                instance=instance, user=request.user
            )
            context["need_add_item"] = True

        serializer = self.serializer_class(instance, context=context)
        return Response(serializer.data)

    @method_permission_classes((IsAuthenticated,))
    def put(self, request, *args, **kwargs):
        serializer = OrganizationUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = OrganizationService.get(id=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))
        updated_organization = OrganizationService.update(
            organization=organization, **serializer.validated_data
        )
        return Response(
            self.serializer_class(
                updated_organization, context={"request": request}
            ).data
        )


class OrganizationPaymentSystemsActivationView(RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        organization = self.get_object()
        payment_systems_activated = organization.payment_systems_activated
        payment_with_confirmation = organization.payment_with_confirmation
        return Response(
            {
                "payment_systems_activated": payment_systems_activated,
                "payment_with_confirmation": payment_with_confirmation,
            },
            status=status.HTTP_200_OK,
        )

    def get_object(self):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=self.request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))
        return organization

    def update(self, request, *args, **kwargs):
        organization = self.get_object()
        payment_systems_activated = request.data.get("payment_systems_activated", None)
        payment_with_confirmation = request.data.get("payment_with_confirmation", None)

        if payment_systems_activated is not None:
            organization.payment_systems_activated = payment_systems_activated
            organization.save()

        if payment_with_confirmation is not None:
            organization.payment_with_confirmation = payment_with_confirmation
            organization.save()

        return Response(
            {"message": _("Payment systems settings updated.")},
            status=status.HTTP_200_OK,
        )


class OrganizationPaymentSystemsActivationDetailView(RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=self.request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))
        return organization

    def update(self, request, *args, **kwargs):
        organization = self.get_object()

        id = request.data.get("id", None)
        is_active = request.data.get("is_active", None)

        if id == 1:
            organization.freedompay_activated = is_active
            organization.save()
        elif id == 2:
            organization.paysy_activated = is_active
            organization.save()
        elif id == 3:
            organization.libersave_activated = is_active
            organization.save()
        elif id == 4:
            organization.betapay_activated = is_active
            organization.save()
        elif id == 5:
            organization.cryptocloud_activated = is_active
            organization.save()
        else:
            raise NotAcceptableException(_("Unknown Payment System"))

        return Response(
            {"message": _("Activation status successfully updated.")},
            status=status.HTTP_200_OK,
        )


class DeliverySettingsView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeliverySettingsUpdateSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data)

    def get_object(self):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=self.request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))
        return organization

    def put(self, request, *args, **kwargs):
        try:
            return super().put(request, *args, **kwargs)
        except ValidationError as error:
            return Response(
                data={"message": _("Invalid input"), "errors": error.detail},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )


class DeactivateOrganizationView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        deactivated_organization = OrganizationService.deactivate(
            organization=organization
        )

        return Response(
            self.serializer_class(
                deactivated_organization, context={"request": request}
            ).data
        )


class ReactivateOrganizationView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        deactivated_organization = OrganizationService.reactivate(
            organization=organization
        )

        return Response(
            self.serializer_class(
                deactivated_organization, context={"request": request}
            ).data
        )


class ResetPurchaseIDView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationDetailedSerializer

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        OrganizationService.reset_running_purchase_id(organization=organization)
        return Response(
            data={"message": _("Successfully reset running purchase ID")},
            status=status.HTTP_200_OK,
        )


class OrgPhonesListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        numbers = OrgPhoneNumberService.get_numbers_of_organization(
            organization_id=kwargs["pk"]
        )
        data = OrgPhoneNumberSerializer(numbers, many=True).data
        return Response(data)

    def post(self, request, **kwargs):
        serializer = OrgPhoneNumberEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        numbers = OrgPhoneNumberService.update_phone_numbers(
            organization_id=kwargs["pk"],
            user=request.user,
            numbers=serializer.validated_data["phone_numbers"],
        )
        data = OrgPhoneNumberSerializer(numbers, many=True).data
        return Response(
            data={"message": _("Successfully updated"), "numbers": data},
            status=status.HTTP_200_OK,
        )


class OrgNetworksListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        networks = OrgSocialNetworkContactService.get_networks_of_organization(
            organization_id=kwargs["pk"]
        )
        data = OrgSocialNetworkContactSerializer(networks, many=True).data
        return Response(data)

    def post(self, request, **kwargs):
        serializer = OrgSocialNetworkEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        networks = OrgSocialNetworkContactService.update_social_networks(
            organization_id=kwargs["pk"],
            user=request.user,
            urls=serializer.validated_data["networks"],
        )
        data = OrgSocialNetworkContactSerializer(networks, many=True).data
        return Response(
            data={"message": _("Successfully updated"), "networks": data},
            status=status.HTTP_200_OK,
        )


class SetOrganizationLocationAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = LocationSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = OrganizationService.get(pk=pk)

        if not OrganizationService.user_can_edit_organization(
            organization=organization, user=request.user
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        changed_organization = OrganizationService.set_location(
            organization=organization,
            longitude=serializer.validated_data.get("longitude"),
            latitude=serializer.validated_data.get("latitude"),
            address=serializer.validated_data.get("address"),
        )

        data = OrganizationSerializer(
            changed_organization, context={"request": request}
        ).data

        return Response(
            data={"message": _("Successfully updated"), "data": data},
            status=status.HTTP_200_OK,
        )


class HomepageOrganizationsView(ListAPIView):
    serializer_class = HomepageOrganizationsSerializer
    partner = None
    country = None
    city = None

    def get_queryset(self):
        serializer = PartnerQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _("Valid partner id, country and city are required in query parameters")
            )
        self.partner = serializer.validated_data["partner"]
        self.city = serializer.validated_data["city"]
        if self.city is None:
            self.country = serializer.validated_data["country"]

        return OrganizationCategoryService.get_nonempty_categories(
            partner=self.partner, country=self.country, city=self.city
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["partner"] = self.partner
        context["country"] = self.country
        context["city"] = self.city
        context["request"] = self.request
        return context


class OrganizationsInCategoryView(ListAPIView):
    filter_backends = (SearchFilter,)
    search_fields = ("title",)
    serializer_class = OrganizationWithDiscountsSerializer

    def get_queryset(self):
        serializer = OrganizationAndCategorySerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _(
                    "Valid category, partner id, country and city are required in query parameters"
                )
            )

        category = serializer.validated_data["category"]
        partner = serializer.validated_data["partner"]
        country = serializer.validated_data["country"]
        city = serializer.validated_data["city"]

        queryset = OrganizationService.get_organizations_in_category(
            category=category, partner=partner, country=country, city=city
        )
        return queryset


class OrganizationsInServicesView(ListAPIView):
    serializer_class = OrganizationServiceSerializer
    queryset = Organization.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(
                _("Valid country, city  are required in query parameters")
            )

        country = serializer.validated_data["country"]
        city = serializer.validated_data["city"]
        subcategory = serializer.validated_data["subcategory"]
        try:
            service = Service.objects.get(id=self.kwargs["pk"])
        except ObjectDoesNotExist:
            raise ObjectNotFoundException
        queryset = OrganizationService.get_organizations_in_service(
            service=service,
            country=country,
            city=city,
            subcategory=subcategory,
            request=self.request,
        )
        return queryset

    def list(self, request, *args, **kwargs):
        has_page = "page" in request.query_params
        has_limit = "limit" in request.query_params

        if not has_page and not has_limit:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)

            return Response(serializer.data)
        else:
            # С пагинацией
            response = super().list(request, *args, **kwargs)
            response.data["name"] = (
                Service.objects.filter(id=self.kwargs["pk"])
                .values_list("name", flat=True)
                .first()
            )
            return response


class ItemsInServiceView(ListAPIView):
    serializer_class = ItemFeedSerializer
    queryset = ShopItem.objects.all()
    filter_backends = [SearchFilter, FeedItemOrderingFilter]
    search_fields = ["name"]
    filter_class = FeedItemFilter 

    def get_queryset(self):
        ordering = self.request.query_params.get("ordering")  
        serializer = OrganizationCoutrySerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)

        country = serializer.validated_data.get("country")
        city = serializer.validated_data.get("city")
        subcategory = serializer.validated_data.get("subcategory")

        service_id = self.kwargs.get("pk")
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise ObjectNotFoundException
        queryset = ItemService.get_items_in_service(
            request=self.request,
            service=service,
            country=country,
            city=city,
            subcategory=subcategory,
            ordering=ordering
        )
        return ShopItemService.annotate_likes_and_bookmarks(
            queryset=queryset, user=self.request.user
        )

    def list(self, request, *args, **kwargs):
        has_page = "page" in request.query_params
        has_limit = "limit" in request.query_params

        if not has_page and not has_limit:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)

            return Response(serializer.data)
        else:
            response = super().list(request, *args, **kwargs)
            response.data["name"] = (
                Service.objects.filter(id=self.kwargs["pk"])
                .values_list("name", flat=True)
                .first()
            )
            return response


class HomepageSearchView(ListAPIView):
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ("title",)
    filterset_fields = (
        "country",
        "city",
    )
    serializer_class = OrganizationWithDiscountsSerializer

    def get_queryset(self):
        serializer = PartnerQueryParamSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)
        partner = serializer.validated_data["partner"]
        if partner is None:
            return Organization.active_organizations.filter(is_active=True).exclude(
                subscription_status=TEST
            )

        return OrganizationService.get_organization_partners(
            organization=partner
        ).exclude(subscription_status=TEST)


class SubscriptionsMessageListAPIView(ListAPIView):
    serializer_class = SubscriptionsMessageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("organization",)

    def get_queryset(self):
        messages = OrgMessageService.get_messages_of_organization(
            organization_id=self.request.GET["organization"]
        )
        return messages

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data["wallpapers"] = CommentService.get_wallpapers()
        return response


class OrgMessageAPIView(ListAPIView):
    serializer_class = OrgMessageSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        messages = OrgMessageService.get_messages_of_organization(
            organization_id=self.kwargs["pk"]
        )
        return messages

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data["wallpapers"] = CommentService.get_wallpapers()
        return response

    def post(self, request, *args, **kwargs):
        serializer = OrgMessageCreateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = OrganizationService.get(pk=kwargs["pk"])

        if not OrganizationService.user_can_send_message(
            organization_id=kwargs["pk"], user=request.user
        ):
            raise PermissionDenied(
                {
                    "message": _(
                        "No rights to send message to followers of this organization"
                    )
                }
            )
        OrgMessageService.send_message(
            organization=organization,
            content=serializer.validated_data.get("content"),
            sender=request.user,
            message_to=serializer.validated_data.get("message_to"),
        )
        return Response(
            data={"message": _("Message is created")}, status=status.HTTP_201_CREATED
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request

        return context


class OrganizationTitleRetrieveAPIView(RetrieveAPIView):
    serializer_class = OrganizationTitleSerializer
    queryset = OrganizationService.filter()

    def get_serializer_context(self):
        context = super(OrganizationTitleRetrieveAPIView, self).get_serializer_context()
        context["request"] = self.request

        return context


class InstagramAccountAPIView(APIView):
    def post(self, request):
        serializer = InstagramIntegrationCreateUpdateSerializer(
            data=request.data, many=False
        )

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        data = OrganizationInstagramIntegrationService.check_instagram_account(
            url=serializer.validated_data.get("url")
        )
        return Response(
            data=dict(url=serializer.validated_data.get("url"), user_profile=data),
            status=status.HTTP_200_OK,
        )


class InstagramParseLastDataAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            organization=organization, user=request.user
        ):
            raise PermissionDenied({"message": _("No rights to edit organization")})
        if not InstagramIntegration.objects.get(organization=organization):
            raise ObjectNotFoundException(_("Instagram Integration Link not found"))
        transaction.on_commit(
            lambda: parse_instagram_to_shop_items.delay(
                organization_id=organization.id, posts_count=20, anonymous=True
            )
        )
        return Response({"message": _("Success")})


class InstagramIntegrationCreateRetrieveAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            organization=organization, user=request.user
        ):
            raise PermissionDenied({"message": _("No rights to edit organization")})
        data = OrganizationInstagramIntegrationService.get_from_org(
            organization=organization
        )
        return Response(
            InstagramIntegrationLinkSerializer(data, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        serializer = InstagramIntegrationCreateUpdateSerializer(
            data=request.data, many=False
        )

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = OrganizationService.get(pk=kwargs["pk"])

        if not OrganizationService.user_can_edit_organization(
            organization=organization, user=request.user
        ):
            raise PermissionDenied({"message": _("No rights to edit organization")})
        host = request.META.get("HTTP_HOST", "test.apofiz.com")
        instance = OrganizationInstagramIntegrationService.create(
            organization=organization,
            url=serializer.validated_data.get("url"),
            host=host,
        )
        data = InstagramIntegrationLinkSerializer(
            instance, context={"request": request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        organization = OrganizationService.get(pk=kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            organization=organization, user=request.user
        ):
            raise PermissionDenied({"message": _("No rights to edit organization")})
        OrganizationInstagramIntegrationService.delete(organization=organization)
        return Response({"message": _("Successfully deleted")})


class OrganizationFollowersCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        users = SubscriptionService.get_organization_followers(organization_id=pk)[:3]
        count = SubscriptionService.get_organization_followers(
            organization_id=pk
        ).count()

        return Response(
            data={
                "followers": UserShortInfoSerializer(
                    users, many=True, context={"request": request}
                ).data,
                "count": count,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationPartnersCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        organization = OrganizationService.get(id=pk)
        count, partners = OrganizationService.get_partners_dict(
            organization=organization
        )

        return Response(
            data={
                "partners": OrganizationWithImageSerializer(
                    partners, many=True, context={"request": request}
                ).data,
                "count": count,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationPartnersFollowersCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        users = SubscriptionService.get_organization_partners_followers(
            organization_id=pk
        )[:3]
        count = SubscriptionService.get_organization_partners_followers(
            organization_id=pk
        ).count()

        return Response(
            data={
                "followers": UserShortInfoSerializer(
                    users, many=True, context={"request": request}
                ).data,
                "count": count,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationClientDetailsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        user = OrganizationService.get_online_client(
            organization_id=kwargs["organization_id"],
            requested_by=self.request.user,
            user_id=kwargs["user_id"],
        )
        data = FollowerOrClientSerializer(
            user,
            context={"request": request, "organization_id": kwargs["organization_id"]},
        ).data
        return Response(data, status=status.HTTP_200_OK)


class OrganizationComplaintCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = OrganizationComplaint.objects.all()
    serializer_class = OrganizationComplaintSerializer

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except IntegrityError:
            raise IntegrityException(_("You have already complained about this item"))


class OrganizationBlackListCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = OrganizationBlacklist.objects.all()
    serializer_class = OrganizationBlacklistSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)


class OrganizationBlackListDestroyView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        try:
            blacklist = OrganizationBlacklist.objects.get(
                user=self.request.user, organization_id=self.kwargs["pk"]
            ).delete()
            return Response(
                data={
                    "message": _("Successfully deleted"),
                },
                status=status.HTTP_200_OK,
            )
        except OrganizationBlacklist.DoesNotExist:
            raise ObjectNotFoundException(_("OrganizationBlacklist not found"))


class BlockUserCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, IsAnyOrganizationOwnerOrAdmin)
    serializer_class = BlockedUserSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)


class UnblockUserDestroyView(DestroyAPIView):
    permission_classes = (IsAuthenticated, IsAnyOrganizationOwnerOrAdmin)

    def destroy(self, request, *args, **kwargs):
        try:
            blocked_user = BlockedUser.objects.get(
                user_id=self.kwargs["user_id"],
                organization_id=self.kwargs["organization_id"],
            ).delete()
            return Response(
                data={
                    "message": _("Successfully unblocked"),
                },
                status=status.HTTP_200_OK,
            )
        except BlockedUser.DoesNotExist:
            raise ObjectNotFoundException(_("BlockedUser not found"))


class OrganizationPaymentSystemListView(generics.ListAPIView):
    serializer_class = PaymentSystemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        organization_id = self.kwargs.get("pk")

        organization = OrganizationService.get(id=organization_id)

        confirmed_payment_systems = []
        if organization.freedompay_confirmed:
            confirmed_payment_systems.append(
                {
                    "id": 1,
                    "name": "FreedomPay оплата в KGS",
                    "is_active": organization.freedompay_activated,
                }
            )
        if organization.paysy_confirmed:
            confirmed_payment_systems.append(
                {
                    "id": 2,
                    "name": "PaySy в USD",
                    "is_active": organization.paysy_activated,
                }
            )
        if organization.libersave_confirmed:
            confirmed_payment_systems.append(
                {
                    "id": 3,
                    "name": "Libersave в EUR",
                    "is_active": organization.libersave_activated,
                }
            )
        if organization.betapay_confirmed:
            confirmed_payment_systems.append(
                {
                    "id": 4,
                    "name": "Betapay в EUR",
                    "is_active": organization.betapay_activated,
                }
            )
        if organization.cryptocloud_confirmed:
            confirmed_payment_systems.append(
                {
                    "id": 5,
                    "name": "CryptoCloud в USD",
                    "is_active": organization.cryptocloud_activated,
                }
            )

        return confirmed_payment_systems

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PaymentSystemListView(generics.ListAPIView):
    serializer_class = PaymentSystemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        organization_id = self.request.query_params.get("organization_id", None)
        if organization_id is None:
            return []

        organization = OrganizationService.get(pk=organization_id)
        available_payment_systems = []
        if not organization.freedompay_confirmed:
            available_payment_systems.append(
                {"id": 1, "name": "FreedomPay оплата в KGS", "is_available": True}
            )
        if not organization.paysy_confirmed:
            available_payment_systems.append(
                {"id": 2, "name": "PaySy в TRC", "is_available": False}
            )
        if not organization.libersave_confirmed:
            available_payment_systems.append(
                {"id": 3, "name": "Libersave в EUR", "is_available": False}
            )
        if not organization.betapay_confirmed:
            available_payment_systems.append(
                {"id": 4, "name": "Betapay в EUR", "is_available": False}
            )

        return available_payment_systems

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrganizationSubscriptionToGlobalAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        organization_id = 2180

        organization = OrganizationService.get(id=organization_id)

        users_to_subscribe = User.objects.all().exclude(phone_number__startswith="+996")

        for user in users_to_subscribe:
            if Subscription.objects.filter(
                organization=organization, user=user
            ).exists():
                continue

            Subscription.objects.create(
                organization=organization, user=user, status="subscribed"
            )

        return Response(
            {"message": "Subscriptions created successfully."},
            status=status.HTTP_201_CREATED,
        )


class DeleteSubscriptionsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        organization_id = 2180
        organization = OrganizationService.get(id=organization_id)
        try:
            subscriptions = Subscription.objects.filter(organization=organization)
            for sub in subscriptions:
                sub.delete()
            return Response(
                {"message": "Subscriptions deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Subscription.DoesNotExist:
            return Response(
                {"message": "Subscriptions not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class RegionalTariffListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RegionalTariffSerializer

    def get_queryset(self):
        serializer = CountryQueryParamSerializer(data=self.request.GET)
        serializer.is_valid(raise_exception=True)
        country = serializer.validated_data["country"]

        return RegionalTariff.objects.filter(country=country)


class PurchaseOrgSubscriptionView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseOrgSubscriptionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        tariff = serializer.validated_data["tariff"]
        promocode = serializer.validated_data.get("promocode")
        utc_offset_minutes = serializer.validated_data["utc_offset_minutes"]

        user_subscription = UserOrgSubscriptionService.create_user_org_subscription(
            user=request.user,
            processed_by=organization.owner,
            organization=organization,
            tariff=tariff,
            promocode=promocode,
            utc_offset_minutes=utc_offset_minutes,
        )

        return Response(
            {
                "message": _("Success"),
                "transaction_id": user_subscription.transaction_id,
            }
        )


class OrganizationBannerListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationBannerSerializer

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=self.request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))
        return OrganizationService.get_organization_banners(organization=organization)


class AddCustomBannerView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_edit_organization(
            user=self.request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        serializer = OrganizationBannerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        banner = serializer.save()
        organization.banners.add(banner)
        banner_serializer = OrganizationBannerSerializer(banner)
        return Response(banner_serializer.data, status=status.HTTP_201_CREATED)


class RemoveCustomBannerView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        banner = OrganizationBannerService.get(id=self.kwargs["pk"], is_default=False)

        organization = banner.organizations.first()
        if not organization:
            return Response(
                {"detail": "Баннер не привязан ни к одной организации."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not OrganizationService.user_can_edit_organization(
            user=self.request.user, organization=organization
        ):
            raise NotAcceptableException(_("No rights to edit organization"))

        organization.banners.remove(banner)

        if banner.organizations.count() == 0:
            banner.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
