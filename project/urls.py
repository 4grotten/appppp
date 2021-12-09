from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

from notifications.views import CustomFCMDeviceAuthorizedViewSet, FCMDeviceSettingsAPIView

v1 = ([
        path('', include('users.urls')),
        path('', include('organizations.urls')),
        path('', include('common.urls')),
        path('', include('transactions.urls')),
        path('', include('shop.urls')),
        path('', include('delivery.urls')),
        path('', include('cors.urls')),
        path('notifications/', include('notifications.urls'))
      ], 'v1')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(v1)),
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('api/v1/devices/', CustomFCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
    path('api/v1/devicesSettings/', FCMDeviceSettingsAPIView.as_view(), name='device_settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.MONITORING:
    urlpatterns += path('', include('django_prometheus.urls')),
