from django.urls import path

from .views import NotificationListAPIView, NotificationSettingAPIView

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='own_notifications'),
    path('settings/', NotificationSettingAPIView.as_view(), name='notification_setting')
]
