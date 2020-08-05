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
            raise ValidationException('Max number of ids should be less than equal 20')

        return super(MultipleListFilter, self).filter(qs, values).distinct()


class TransactionFilter(filters.FilterSet):
    organization = MultipleListFilter()
    start = filters.DateFilter(field_name="updated_at", lookup_expr='gte')
    end = filters.DateFilter(field_name="updated_at", lookup_expr='lte')

    class Meta:
        model = Transaction
        fields = ('organization_id', 'start', 'end')
