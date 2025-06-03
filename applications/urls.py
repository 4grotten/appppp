from django.urls import path, include

from applications.views import UserAppListCreateView, ToggleUserAppView, UserAppRetrieveUpdateView, \
    UserAppBannerListView, RemoveUserAppCustomBannerView, AddCustomUserAppBannerView, UserAppStoreListView, \
    UserAppCategoryListView

user_app_urls = [
    path('applications/', UserAppListCreateView.as_view(), name='user_applications'),
    path('applications/<int:pk>/', UserAppRetrieveUpdateView.as_view(), name='user_application_detail'),
    path('applications/<int:pk>/banners/', UserAppBannerListView.as_view(), name='user_application_banners'),
    path('applications/banners/<int:pk>/', RemoveUserAppCustomBannerView.as_view(),
         name='application-banners-delete'),
    path('applications/<int:pk>/banners/custom/', AddCustomUserAppBannerView.as_view(),
         name='add_user_app_custom_banner'),
    path('applications/<int:pk>/toggle/', ToggleUserAppView.as_view(), name='toggle_user_app'),
    path('applications/categories/', UserAppCategoryListView.as_view(), name='user_app_categories'),
    path('applications/store/', UserAppStoreListView.as_view(), name='user_apps_list')
]
urlpatterns = [
    path('', include(user_app_urls)),
]

