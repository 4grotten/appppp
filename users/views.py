from decimal import Decimal

from django.contrib.auth import authenticate
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView, DestroyAPIView, ListCreateAPIView, \
    RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from transliterate.utils import _

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.models import UmaiWallet, BlockedIps, TemporaryCodeSwitcher
from common.pagination import GeneralPagination
from common.services import slack
from common.services.umai import Umai
from notifications.constants import NOTIFICATION_MODE_SYSTEM, NEW_DEVICE, NEW_DEVICE_TITLE
from organizations.models import Subscription, Organization, UserOrgSubscription
from organizations.serializers.organization_serializers import OrganizationWithUsersSerializer
from .constants import CHANGE_AUTH_NUMBER_TYPE, REGISTER_AUTH_TYPE, DEVICE_TYPES, WHATSAPP_AUTH_TYPE, VOICE_AUTH_TYPE, \
    EMAIL_AUTH_TYPE
from .models import MyOwnToken, User, DeliveryAddress, PromoCode, ReferralBalance, ReferralTransaction
from .serializers import (
    RegisterAuthSerializer, TemporaryCodeSerializer, LoginSerializer,
    ResendTemporaryCodeSerializer, ProfileUpdateSerializer, ProfileSerializer,
    SetPasswordSerializer, UserChangePasswordSerializer, ForgotPasswordSerializer,
    SendCodeToNewNumberSerializer, PhoneNumberEditSerializer, SocialNetworkEditSerializer,
    PhoneNumberSerializer, SocialNetworkContactSerializer, ChangeAndValidateNewNumberSerializer, MyOwnTokenSerializer,
    MyOwnTokenExpiredTimeSerializer, DeliveryAddressesSerializer, SetDefaultDeliveryAddressSerializer,
    PromoCodeValidationSerializer, PromoCodeSerializer, ReferralBalanceSerializer, ReferralTransactionSerializer,
    ReferralStatsSerializer, ReferredUserWithOrganizationsSerializer,
)
from notifications.tasks import sent_notification
from .services import (
    UserService, TemporaryCodeService, PhoneNumberService, SocialNetworkContactService, TemporaryPhoneNumberService,
    MyOwnTokenService, DeliveryAddressesService, PromoCodeService
)
from .throttle.throttle import UserLoginRateThrottle

class RegisterAuthAPIView(APIView):
    permission_classes = ()
    authentication_classes = ()
    throttle_classes = (UserLoginRateThrottle,)

    def throttled(self, request, wait):
        if 'recaptcha' in request.data:
            raise Throttled(detail={
                "message": "recaptcha_required",
            })

    def post(self, request):
        serializer = RegisterAuthSerializer(data=request.data)

        ip = request.META.get('REMOTE_ADDR', '')
        if BlockedIps.objects.filter(ip_address=ip).first():
            return Response(status=403, data={'message': "Forbidden"})

        if not serializer.is_valid():
            return Response(
                data={
                    'message': gettext_lazy('Invalid input'),
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        token = None
        phone_number = serializer.validated_data.get('phone_number')

        try:
            temporary_code_enabled = TemporaryCodeSwitcher.objects.last().is_enable
        except:
            temporary_code_enabled = True
        if not UserService.filter(phone_number=phone_number).exists():
            ip = request.META.get('REMOTE_ADDR', '')
            user = UserService.create(phone_number=phone_number)

            if temporary_code_enabled:
                TemporaryCodeService.create_and_send(user=user, ip_addr=ip)
            elif str(phone_number).startswith("+996"):
                TemporaryCodeService.create_and_send(user=user, ip_addr=ip)
            else:
                token = MyOwnTokenService.get_or_create_token(user=user, request=request)

            return Response(data={
                'message': gettext_lazy('User has successfully created'),
                'is_new_user': user.is_new_user,
                'token': token.key if token else None,
                'temporary_code_enabled': temporary_code_enabled
            })


        user = UserService.get(phone_number=phone_number)

        if not user.is_active:
            return Response(
                data={
                    'message': _('User deleted')
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if user.is_new_user:
            if TemporaryCodeService.filter(user=user, is_used=True).exists() or not temporary_code_enabled:
                token = MyOwnTokenService.get_or_create_token(user=user, request=request)
            else:
                ip = request.META.get('REMOTE_ADDR', '')
                TemporaryCodeService.create_and_send(user=user, ip_addr=ip)

        return Response(data={
            'message': gettext_lazy('User found'),
            'is_new_user': user.is_new_user,
            'token': token.key if token else None,
            'email': True if user.email else False,
        })


class VerifyTemporaryCodeAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = TemporaryCodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        code = serializer.validated_data.get('code')
        phone_number = serializer.validated_data.get('phone_number')

        TemporaryCodeService.validate(code=code, phone_number=phone_number)

        user = UserService.get(phone_number=phone_number)

        try:
            token = MyOwnToken.objects.get(user=user, is_active=True, ip=request.META.get('REMOTE_ADDR'))
        except MyOwnToken.DoesNotExist:
            token = MyOwnToken.objects.create(user=user, ip=request.META.get('REMOTE_ADDR'))
            token.save()
        except MyOwnToken.MultipleObjectsReturned:
            tokens = MyOwnToken.objects.filter(user=user, is_active=True, ip=request.META.get('REMOTE_ADDR')).order_by(
                '-log_time')
            token = tokens.latest('log_time')
        slack.bot(f'User {user} successfully validated\n'
                  f'============================')

        return Response(data={
            'message': gettext_lazy('Successfully validated'),
            'token': token.key if token else None,
            'is_new_user': user.is_new_user
        }, status=status.HTTP_200_OK)


class ResendTemporaryCodeAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = ResendTemporaryCodeSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        resend_type = serializer.validated_data.get('type')
        phone_number = serializer.validated_data.get('phone_number')
        ip = request.META.get('REMOTE_ADDR', '')
        if resend_type == CHANGE_AUTH_NUMBER_TYPE:
            temporary_codes = TemporaryPhoneNumberService.filter(phone_number=phone_number)
            if not temporary_codes:
                raise ObjectNotFoundException(gettext_lazy('You can not resend'))

            temporary_code = temporary_codes.last()

            TemporaryPhoneNumberService.create(user=temporary_code.user, phone_number=phone_number)

        elif resend_type == REGISTER_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user, ip_addr=ip)

        elif resend_type == WHATSAPP_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user, whatsapp=True, ip_addr=ip)

        elif resend_type == EMAIL_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user, email=True, ip_addr=ip)

        elif resend_type == VOICE_AUTH_TYPE:
            # ToDo voice auth type
            pass

        return Response(data={
            'message': gettext_lazy('Code has successfully sent')
        }, status=status.HTTP_200_OK)


class ProfileInitialAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=UserService.get_data_with_valid_location(request), many=False, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        is_new_in_begin = request.user.is_new_user
        if is_new_in_begin:
            MyOwnTokenService.save_device_info(request=request, serializer=serializer)



        user = UserService.init_profile(
            user=request.user,
            avatar_id=serializer.validated_data.get('avatar_id'),
            username=serializer.validated_data.get('username', None),
            date_of_birth=serializer.validated_data.get('date_of_birth', None),
            gender=serializer.validated_data.get('gender', None),
            full_name=serializer.validated_data.get('full_name'),
            email=serializer.validated_data.get('email', None),
        )

        registration = UmaiWallet.objects.last()
        device_type = serializer.validated_data.get('device_type')
        if device_type in DEVICE_TYPES and registration and registration.is_accepted and \
                str(user.phone_number).startswith("+996") and is_new_in_begin:
            Umai(str(user.phone_number), wallet=registration).commit_payment()
        if user.full_name != None:
            apofiz_org = Organization.objects.get(title='Apofiz.com')
            subscription, created = Subscription.objects.get_or_create(user=user, organization=apofiz_org)

        slack.bot(f'User {user} has successfully registered\n'
                  f'============================')
        return Response(ProfileSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)


class SetPasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserService.set_password(user=request.user, password=serializer.validated_data.get('password'))

        return Response(data={
            'message': gettext_lazy('You have successfully set password')
        }, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=UserService.get_data_with_valid_location(request))

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = authenticate(**serializer.validated_data)

        if user is not None:
            device_info = MyOwnTokenService.get_device_info(serializer=serializer, request=request)
            location = UserService.get_location_info(serializer=serializer)

            token = MyOwnTokenService.get_or_create_token(user=user, request=request, location=location, device_info=device_info)

            user_data = ProfileSerializer(user, context={'request': request}).data

            transaction.on_commit(lambda: sent_notification.delay(
                recipient_id=user.id,
                mode=NOTIFICATION_MODE_SYSTEM,
                notification_type=NEW_DEVICE,
                title=NEW_DEVICE_TITLE,
                extra_data=dict(device_title=device_info['device'], location=location, created_at=token.created_at)
            ))

            return Response(data={
                'message': gettext_lazy('Successfully logged in'),
                'token': token.key,
                'user': user_data
            }, status=status.HTTP_200_OK)

        return Response(data={
            'message': gettext_lazy('Wrong credentials'),
            'errors': {}
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # ToDo: MULTI-TOKEN AUTH
        token_key = request.headers['Authorization'].split()[1]
        MyOwnToken.objects.filter(key=token_key).update(is_active=False)

        return Response(data={
            'message': gettext_lazy('Successfully logged out'),
        }, status=status.HTTP_200_OK)


class UserChangePasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = UserChangePasswordSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserService.change_password(
            user=request.user,
            old_password=serializer.validated_data.get('old_password', None),
            new_password=serializer.validated_data.get('new_password', None)
        )

        return Response(data={'message': gettext_lazy('Password has successfully changed')}, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        ip = request.META.get('REMOTE_ADDR', '')
        user = UserService.get(phone_number=serializer.validated_data.get('phone_number'))
        TemporaryCodeService.create_and_send(user=user, ip_addr=ip)

        #        input_type = serializer.validated_data.get('type')

        #        if input_type == PHONE_NUMBER_TYPE:
        #            user = UserService.get(phone_number=serializer.validated_data.get('phone_number'))
        #            TemporaryCodeService.create_and_send(user=user)
        #        elif input_type == EMAIL_TYPE:
        #            user = UserService.get(email=serializer.validated_data.get('email'))
        #            # TODO send code to email
        #        else:
        #            raise ValidationException(_('Invalid input'))

        return Response(data={
            'message': gettext_lazy('Code sent')
        }, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        return Response(ProfileSerializer(user, context={'request': request}).data)


class UserPhonesListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        numbers = PhoneNumberService.get_numbers_of_user(user_id=kwargs['pk'])
        data = PhoneNumberSerializer(numbers, many=True).data
        return Response(data)


class UserPhoneNumbersUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PhoneNumberEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        numbers = PhoneNumberService.update_phone_numbers(user=request.user,
                                                          numbers=serializer.validated_data['phone_numbers'])
        data = PhoneNumberSerializer(numbers, many=True).data
        return Response(data={
            'message': gettext_lazy('Successfully updated'),
            'numbers': data
        }, status=status.HTTP_200_OK)


class UserSocialNetworksListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        networks = SocialNetworkContactService.get_networks_of_user(user_id=kwargs['pk'])
        data = SocialNetworkContactSerializer(networks, many=True).data
        return Response(data)


class UserSocialNetworksUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SocialNetworkEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        networks = SocialNetworkContactService.update_social_networks(user=request.user,
                                                                      urls=serializer.validated_data['networks'])
        data = SocialNetworkContactSerializer(networks, many=True).data
        return Response(data={
            'message': gettext_lazy('Successfully updated'),
            'networks': data
        }, status=status.HTTP_200_OK)


class UserDeliveryAddressesListAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeliveryAddressesSerializer

    def get(self, request, **kwargs):
        addresses = DeliveryAddressesService.get_addresses_of_user(user=request.user)
        data = self.serializer_class(addresses, many=True).data
        return Response(data)

    def post(self, request, *args, **kwargs):
        serializer = DeliveryAddressesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        DeliveryAddressesService.create(user=request.user, **serializer.validated_data)

        return Response(data={'message': _('Successfully created delivery address')}, status=status.HTTP_201_CREATED)


class UserDeliveryAddressDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeliveryAddressesSerializer

    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)


class SetDefaultDeliveryAddressAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SetDefaultDeliveryAddressSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        address_id = serializer.validated_data['address_id']

        DeliveryAddressesService.set_default_delivery_address(address_id=address_id, user=request.user)

        return Response(data={'message': _('Default delivery address updated successfully')}, status=status.HTTP_200_OK)


class ValidateOldNumberAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        ip = request.META.get('REMOTE_ADDR', '')

        temporary_code_enabled = TemporaryCodeSwitcher.objects.last().is_enable

        if temporary_code_enabled:
            TemporaryCodeService.create_and_send(user=request.user, ip_addr=ip)

        return Response(data={
            'message': gettext_lazy('Code sent to old number and email')
        })


class ChangeAndVerifyNewNumber(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangeAndValidateNewNumberSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        old_phone_number = serializer.validated_data.get('old_phone_number')

        user = UserService.get(phone_number=old_phone_number)

        if user != request.user:
            raise NotAcceptableException(gettext_lazy('You have not permission to do this operation'))

        code = serializer.validated_data.get('code')

        if code is not None:
            TemporaryPhoneNumberService.validate_code_and_phone_number(
                code=serializer.validated_data.get('code'), phone_number=old_phone_number
            )
        else:
            TemporaryPhoneNumberService.validate_phone_number(phone_number=old_phone_number)

        UserService.change_phone_number(
            user=user, new_phone_number=serializer.validated_data.get('new_phone_number')
        )

        return Response(data={
            'message': gettext_lazy('You have successfully changed auth number')
        })


class TemporaryCodeSwitcherStatusView(APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request):

        temporary_code_enabled = TemporaryCodeSwitcher.objects.last().is_enable

        return Response({'sms_service': temporary_code_enabled})


class SendCodeToNewNumberAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SendCodeToNewNumberSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TemporaryPhoneNumberService.create(
            user=request.user,
            phone_number=serializer.validated_data.get('phone_number')
        )

        return Response(data={
            'message': gettext_lazy('Code sent to new phone number')
        })


class GetEmailUserAPIView(APIView):

    def post(self, request):
        serializer = PhoneNumberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': gettext_lazy('Invalid input'),
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        phone_number = serializer.validated_data['phone_number']
        email = UserService.get_user_email_by_phone_number(phone_number=phone_number)
        return Response({'email': email})


class MyOwnTokenChangeExpiredTimeView(APIView):
    def post(self, request, **kwargs):
        serializer = MyOwnTokenExpiredTimeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': gettext_lazy('Invalid input'),
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        expired_time = serializer.validated_data['expired_time_choice']
        token = MyOwnToken.objects.get(id=self.kwargs['pk'])
        token.expired_time_choice = expired_time
        token.save()
        return Response({'success': True})


class MyOwnTokenListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer
    pagination_class = GeneralPagination

    def get_queryset(self):
        user = self.request.user
        return MyOwnToken.objects.filter(user=user, is_active=True).order_by('-log_time')


class MyOwnTokenRetrieveDestroyView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer

    def get_object(self):
        try:
            return MyOwnToken.objects.get(id=self.kwargs['pk'])
        except MyOwnToken.DoesNotExist:
            return Response(
                data={
                    "Error": _("Invalid id"),
                }, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        MyOwnToken.objects.filter(id=self.kwargs['pk']).update(is_active=False)
        return Response({'message': 'Token deactivated'}, status=status.HTTP_200_OK)


class DestroyAllTokens(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer

    def destroy(self, request, *args, **kwargs):
        MyOwnToken.objects.filter(user=self.request.user).update(is_active=False)
        return Response({'message': 'All tokens of user deactivated'}, status=status.HTTP_200_OK)


class AuthorisationHistoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer
    pagination_class = GeneralPagination

    def get_queryset(self):
        user = self.request.user
        return MyOwnToken.objects.filter(user=user, is_active=False).order_by('-log_time')

class DeactivateUserProfile(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            user = self.request.user
            user.is_active = False
            user.save()
            return Response(
                data={
                    "Success": True,
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                data={
                    "Error": _("User does not exists"),
                }, status=status.HTTP_400_BAD_REQUEST
            )


class UserHasOwnOrganizationOrCanEdit(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            user = self.request.user
            has_organizations = Organization.objects.filter(
                Q(owner=user, is_deleted=False) | Q(memberships__user=user, is_deleted=False,
                                                    memberships__role__can_edit_organization=True)
            ).exists()

            return Response(
                data={
                    "has_organizations": has_organizations,
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                data={
                    "Error": _("User does not exists"),
                }, status=status.HTTP_400_BAD_REQUEST
            )


class MyPromoCodeView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        promo_code, created = PromoCode.objects.get_or_create(owner=request.user)
        serializer = PromoCodeSerializer(promo_code)
        return Response(serializer.data)

    def post(self, request):
        serializer = PromoCodeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['promocode']
        user = request.user

        promo = PromoCodeService.get(code=code)

        if promo.owner == user:
            return Response({"detail": "You can not use your own promocode."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "is_valid": True,
            "discount_percent": promo.discount_percent
        }, status=status.HTTP_200_OK)


class MyReferralBalanceView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        balance, created = ReferralBalance.objects.get_or_create(user=request.user)
        serializer = ReferralBalanceSerializer(balance)
        return Response(serializer.data)


class MyReferralHistoryView(ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ReferralTransactionSerializer

    def get_queryset(self):
        return ReferralTransaction.objects.filter(owner=self.request.user)


class ReferralStatsAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        user = request.user

        promocode = PromoCodeService.get(owner=user)

        transactions = ReferralTransaction.objects.filter(promocode=promocode)

        total_referrals = transactions.values("referred_user").distinct().count()
        total_organizations = transactions.values("subscription__organization").distinct().count()
        total_profit_usdt = transactions.aggregate(total=Sum("profit_amount_usdt"))["total"] or Decimal("0.00")

        data = {
            "total_referrals": total_referrals,
            "total_organizations": total_organizations,
            "total_profit_usdt": total_profit_usdt,
        }

        serializer = ReferralStatsSerializer(data)
        return Response(serializer.data)


class ReferralUsersListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ReferredUserWithOrganizationsSerializer

    def get_queryset(self):
        promocode = PromoCodeService.get(owner=self.request.user)
        referred_users_ids = ReferralTransaction.objects.filter(promocode=promocode).values_list("referred_user",
                                                                                                 flat=True).distinct()
        queryset = User.objects.filter(id__in=referred_users_ids)
        return queryset


class ReferralOrganizationsListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = OrganizationWithUsersSerializer

    def get_queryset(self):
        promocode = PromoCodeService.get(owner=self.request.user)
        transaction_subs = ReferralTransaction.objects.filter(promocode=promocode).values_list("subscription_id",
                                                                                               flat=True)
        org_ids = UserOrgSubscription.objects.filter(id__in=transaction_subs).values_list("organization_id", flat=True)
        queryset = Organization.objects.filter(id__in=org_ids).distinct()

        return queryset
