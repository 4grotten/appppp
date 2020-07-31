from django.urls import path

from .views import NotificationListAPIView, NotificationSettingAPIView, NotificationsCountAPIView

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='own_notifications'),
    path('settings/', NotificationSettingAPIView.as_view(), name='notification_setting'),
    path('statistics/', NotificationsCountAPIView.as_view(), name='notification_count')
]
