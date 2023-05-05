from datetime import timedelta

import django_filters
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters, Filter

from common.exceptions import ValidationException
from transactions.models import Transaction


class MultipleListFilter(Filter):
    MAX_LIMIT = 20

    def filter(self, qs, value):
        if not value:
            return qs

        self.lookup_expr = 'in'
        values = value.split(',')

        if len(values) > self.MAX_LIMIT:
            raise ValidationException(_('Max number of ids should be less than equal 20'))

        return super(MultipleListFilter, self).filter(qs, values).distinct()


class EndFilter(django_filters.DateFilter):

    def filter(self, qs, value):
        if value:
            value = value + timedelta(days=1)
        return super(EndFilter, self).filter(qs, value)


class TransactionFilter(filters.FilterSet):
    organization = MultipleListFilter()
    start = filters.DateFilter(field_name="updated_at", lookup_expr='gte')
    end = EndFilter(field_name="updated_at", lookup_expr='lt')

    class Meta:
        model = Transaction
        fields = ('organization_id', 'start', 'end')


class TransactionRentalFilter(filters.FilterSet):
    start = filters.DateFilter(field_name="updated_at", lookup_expr='gte')
    end = EndFilter(field_name="updated_at", lookup_expr='lt')

    class Meta:
        model = Transaction
        fields = ('start', 'end')
