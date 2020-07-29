from django_filters import rest_framework as filters

from notifications.models import Notification


class NotificationFilter(filters.FilterSet):
    class Meta:
        model = Notification
        fields = ('mode',)