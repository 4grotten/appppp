from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView

from applications.models import AddedApp, UserApp, UserAppCategory, UserAppPurchase, UserAppBalance, UserAppTransaction
from applications.serializers import UserAppCreateSerializer, UserAppDetailedSerializer, UserAppListSerializer, \
    UserAppUpdateSerializer, UserAppBannerSerializer, UserAppBannerCreateSerializer, UserAppCategorySerializer, \
    PurchaseUserAppSerializer, UserAppBalanceSerializer, \
    UserAppPurchasesSerializer, UserAppPurchaseWithProfitSerializer, UserAppChangeVisibilitySerializer
from applications.services import UserAppService, UserAppBannerService
from common.exceptions import NotAcceptableException
from common.utils import method_permission_classes


class UserAppListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        my_apps = UserAppService.filter(owner=user)

        added_apps = UserAppService.filter(addedapp__user=user).exclude(owner=user)

        return Response({
            'my_apps': UserAppListSerializer(my_apps, many=True, context={'request': request}).data,
            'my_added_apps': UserAppListSerializer(added_apps, many=True, context={'request': request}).data
        })

    def create(self, request, *args, **kwargs):
        serializer = UserAppCreateSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = UserAppService.create_application(**serializer.validated_data)

        data = UserAppDetailedSerializer(organization, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class UserAppRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = UserAppDetailedSerializer
    queryset = UserApp.objects.all()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        context = {
            'request': request,
        }

        serializer = self.serializer_class(instance, context=context)
        return Response(serializer.data)

    @method_permission_classes((IsAuthenticated,))
    def put(self, request, *args, **kwargs):
        serializer = UserAppUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        application = UserAppService.get(id=kwargs['pk'])
        if application.owner != request.user:
            raise NotAcceptableException(_('No rights to edit application'))
        validated_data = serializer.validated_data
        image_id = validated_data.pop('image_id')
        updated_application = UserAppService.update(application=application, image_id=image_id,
                                                    validated_data=validated_data)
        return Response(self.serializer_class(updated_application, context={'request': request}).data)


class UserAppBannerListView(ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserAppBannerSerializer

    def get_queryset(self):
        application = UserAppService.get(id=self.kwargs['pk'])
        if application.owner != self.request.user:
            raise NotAcceptableException(_('No rights to edit application'))
        return UserAppService.get_application_banners(application=application)


class RemoveUserAppCustomBannerView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        banner = UserAppBannerService.get(id=self.kwargs['pk'], is_default=False)

        application = banner.user_apps.first()
        if not application:
            return Response({'detail': 'Баннер не привязан ни к одной организации.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if application.owner != self.request.user:
            raise NotAcceptableException(_('No rights to edit application'))

        application.banners.remove(banner)

        if banner.user_apps.count() == 0:
            banner.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AddCustomUserAppBannerView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        application = UserAppService.get(id=self.kwargs['pk'])
        if application.owner != self.request.user:
            raise NotAcceptableException(_('No rights to edit application'))

        serializer = UserAppBannerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        banner = serializer.save()
        application.banners.add(banner)
        banner_serializer = UserAppBannerSerializer(banner)
        return Response(banner_serializer.data, status=status.HTTP_201_CREATED)


class ToggleUserAppView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user_app = UserAppService.get(id=kwargs['pk'])

        if user_app.owner == request.user:
            return Response({"detail": "You cannot add your own app."}, status=status.HTTP_400_BAD_REQUEST)

        added_app, created = AddedApp.objects.get_or_create(
            user=request.user,
            user_app=user_app
        )

        if not created:
            added_app.delete()
            return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Successfully added"}, status=status.HTTP_201_CREATED)


class UserAppCategoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAppCategorySerializer
    queryset = UserAppCategory.objects.all()


class UserAppStoreListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAppListSerializer
    queryset = UserApp.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['types__category']
    search_fields = ['title', 'description']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PurchaseUserAppView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PurchaseUserAppSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        app = serializer.validated_data['app']
        utc_offset_minutes = serializer.validated_data['utc_offset_minutes']

        if UserAppPurchase.objects.filter(user=request.user, app=app, is_paid=True).exists():
            raise NotAcceptableException(_('You already purchased this app.'))

        app_purchase = UserAppService.create_app_purchase(
            user=request.user,
            app=app,
            processed_by=app.owner,
            utc_offset_minutes=utc_offset_minutes
        )

        return Response({
            "message": _("Success"),
            "transaction_id": app_purchase.transaction_id
        })


class UserAppBalanceView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        balance, created = UserAppBalance.objects.get_or_create(user=request.user)
        serializer = UserAppBalanceSerializer(balance)
        return Response(serializer.data)


class UserAppStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        clients_count = UserAppPurchase.objects.filter(
            app__owner=user,
            is_paid=True
        ).exclude(user=user).values('user').distinct().count()

        purchases_count = UserAppPurchase.objects.filter(
            user=user,
            is_paid=True
        ).count()
        total_profit = UserAppTransaction.objects.filter(
            owner=user
        ).aggregate(total=Sum('profit_amount'))['total'] or 0

        return Response({
            "clients_count": clients_count,
            "purchases_count": purchases_count,
            "total_profit": float(total_profit),
        })


class UserSoldAppsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAppListSerializer

    def get_queryset(self):
        return UserApp.objects.filter(
            purchases__is_paid=True,
            owner=self.request.user
        ).exclude(
            purchases__user=self.request.user
        ).distinct()


class AppSoldTransactionsListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserAppPurchaseWithProfitSerializer

    def get_queryset(self):
        app = UserAppService.get(id=self.kwargs['pk'])
        return UserAppPurchase.objects.select_related(
            'app',
            'user',
            'transaction'
        ).prefetch_related(
            'referral_transactions'
        ).filter(
            app=app,
            app__owner=self.request.user,
            is_paid=True
        ).order_by('-created_at')



class UserAppPurchasesListView(ListAPIView):
    queryset = UserAppPurchase.objects.select_related('app', 'transaction')
    serializer_class = UserAppPurchasesSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user, is_paid=True).order_by('-created_at')


class ToggleUserAppVisibilityView(GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        serializer = UserAppChangeVisibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserAppService.update_visibility_status(user=request.user, user_app=serializer.validated_data['app'],
                                                is_hidden=serializer.validated_data['is_hidden'])

        return Response(data={'message': _('Successfully updated visibility status')})