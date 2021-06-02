from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from common.exceptions import ValidationException
from notifications.models import Notification


class MultipleListFilter(filters.Filter):
    MAX_LIMIT = 20

    def filter(self, qs, value):
        if not value:
            return qs

        self.lookup_expr = 'in'
        values = value.split(',')

        if len(values) > self.MAX_LIMIT:
            raise ValidationException(_('Max number of ids should be less than equal 20'))

        return super(MultipleListFilter, self).filter(qs, values).distinct()


class NotificationFilter(filters.FilterSet):
    mode = MultipleListFilter(field_name='mode')

    class Meta:
        model = Notification
        fields = ('mode',)
