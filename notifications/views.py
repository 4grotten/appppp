from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .filters import NotificationFilter
from .serializers import NotificationSerializer
from .services import NotificationService


class NotificationListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = NotificationFilter

    def get_queryset(self):
        return NotificationService.get_own_notifications(user=self.request.user)
