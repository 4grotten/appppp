from django.urls import path, include

from applications.views import UserAppListCreateView, ToggleUserAppView, UserAppRetrieveUpdateView, \
    UserAppBannerListView, RemoveUserAppCustomBannerView, AddCustomUserAppBannerView, UserAppStoreListView, \
    UserAppCategoryListView, PurchaseUserAppView, UserAppBalanceView, UserAppStatsView, UserSoldAppsListView, \
    AppSoldTransactionsListView, UserAppPurchasesListView, ToggleUserAppVisibilityView

user_app_urls = [
    path('applications/', UserAppListCreateView.as_view(), name='user_applications'),
    path('applications/<int:pk>/banners/', UserAppBannerListView.as_view(), name='user_application_banners'),
    path('applications/banners/<int:pk>/', RemoveUserAppCustomBannerView.as_view(),
         name='application-banners-delete'),
    path('applications/<int:pk>/banners/custom/', AddCustomUserAppBannerView.as_view(),
         name='add_user_app_custom_banner'),
    path('applications/<int:pk>/toggle/', ToggleUserAppView.as_view(), name='toggle_user_app'),
    path('applications/categories/', UserAppCategoryListView.as_view(), name='user_app_categories'),
    path('applications/store/', UserAppStoreListView.as_view(), name='user_apps_list'),
    path('applications/purchase/', PurchaseUserAppView.as_view(), name='user_apps_purchase'),
    path('applications/balance/', UserAppBalanceView.as_view(), name='user_apps_balance'),
    path('applications/stats/', UserAppStatsView.as_view(), name='user_apps_stats'),
    path('applications/sold/', UserSoldAppsListView.as_view(), name='user_apps_sold'),
    path('applications/<int:pk>/sold/', AppSoldTransactionsListView.as_view(), name='user_app_sold'),
    path('applications/purchases/', UserAppPurchasesListView.as_view(), name='user_app_purchases'),
    path('applications/toggle-visibility/', ToggleUserAppVisibilityView.as_view(),
         name='toggle-user-app-visibility'),
    path('applications/<slug:slug>/', UserAppRetrieveUpdateView.as_view(), name='user_application_detail'),


]
urlpatterns = [
    path('', include(user_app_urls)),
]

