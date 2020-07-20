from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

v1 = ([
          path('', include('users.urls')),
          path('', include('organizations.urls')),
          path('', include('common.urls')),
          path('', include('transactions.urls')),
          path('', include('notifications.urls'))
      ], 'v1')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(v1)),
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('api/v1/devices/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
