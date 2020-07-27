from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import NotificationSerializer
from .services import NotificationService


class NotificationListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return NotificationService.get_own_notifications(user=self.request.user)
