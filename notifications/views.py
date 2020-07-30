from django_filters.rest_framework import DjangoFilterBackend
from fcm_django.api.rest_framework import AuthorizedMixin, FCMDeviceViewSet
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .filters import NotificationFilter
from .serializers import NotificationSerializer, CustomFCMDeviceSerializer
from .services import NotificationService


class NotificationListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = NotificationFilter

    def get_queryset(self):
        return NotificationService.get_own_notifications(user=self.request.user)


class CustomFCMDeviceAuthorizedViewSet(AuthorizedMixin, FCMDeviceViewSet):
    serializer_class = CustomFCMDeviceSerializer
