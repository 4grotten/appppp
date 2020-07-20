from django.urls import path

from notifications.views import NotificationListAPIView

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='own_notifications')
]
