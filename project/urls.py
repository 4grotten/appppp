from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from django.http import HttpResponseRedirect

from notifications.views import (
    CustomFCMDeviceAuthorizedViewSet,
    FCMDeviceSettingsAPIView,
)

PORTAINER_URL = settings.PORTAINER_URL


def portainer_login(request):
    return HttpResponseRedirect(PORTAINER_URL)


v1 = (
    [
        path("", include("users.urls")),
        path("", include("organizations.urls")),
        path("", include("applications.urls")),
        path("", include("messenger.urls")),
        path("", include("common.urls")),
        path("", include("transactions.urls")),
        path("", include("shop.urls")),
        path("", include("delivery.urls")),
        path("", include("sms_sender.urls")),
        path("", include("cors.urls")),
        path("", include("stock.urls")),
        path("notifications/", include("notifications.urls")),
    ],
    "v1",
)

urlpatterns = [
    path("971585333939admin/portainer-login/", portainer_login, name="portainer_login"),
    path("971585333939admin/", admin.site.urls),
    path("api/v1/", include(v1)),
    path("api-auth/", include("rest_framework.urls")),
    path("rest-auth/", include("rest_auth.urls")),
    path(
        "api/v1/devices/",
        CustomFCMDeviceAuthorizedViewSet.as_view({"post": "create"}),
        name="create_fcm_device",
    ),
    path(
        "api/v1/devicesSettings/",
        FCMDeviceSettingsAPIView.as_view(),
        name="device_settings",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    try:
        from drf_yasg.views import get_schema_view
        from drf_yasg import openapi

        schema_view = get_schema_view(
            openapi.Info(
                title="API Documentation",
                default_version='v1',
                description="Документация доступна только в режиме отладки",
            ),
            public=True,
            permission_classes=(permissions.AllowAny,),
            authentication_classes=[],
        )

        urlpatterns += [
            re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
            path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
            path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        ]
    except ImportError:

        pass

if settings.MONITORING:
    urlpatterns += (path("", include("django_prometheus.urls")),)
