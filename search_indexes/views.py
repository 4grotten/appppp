from django.utils.translation import gettext_lazy as _
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend, FilteringFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from search_indexes.documents.items import ShopItemDocument
from search_indexes.serializers.item import ShopItemsDocumentSerializer
from search_indexes.services.index_services import IndexServices
from shop.serializers.item_serializers import StartDateTimeSerializer
from shop.services.item_services import ShopItemService


class ShopItemDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer
    pagination_class = GeneralPagination

    filter_backends = [
        FilteringFilterBackend,
        DefaultOrderingFilterBackend,
        CompoundSearchFilterBackend,
    ]

    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'article': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'}
    }

    filter_fields = {
        'price': 'price.raw'
    }

    def list(self, request, *args, **kwargs):
        search = request.GET.get('search', None)

        if search and search[0] == '#':  # Search among posts if hashtag is used
            pass
        else:
            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.query_params['price__isnull'] = "false"
            request.query_params._mutable = mutable

        qs = super(ShopItemDocumentView, self).list(request)

        if search:
            symbols = request.query_params['search']
            reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(symbols))
            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.query_params['search'] = reversed_symbols
            request.query_params._mutable = mutable

            qs_r = super(ShopItemDocumentView, self).list(request)

            qs = qs if qs.data['total_count'] >= qs_r.data['total_count'] else qs_r

        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        start_time = serializer.validated_data['start_time']
        if start_time:
            qs.data['has_new'] = ShopItemService.has_new(timestamp=start_time, user=request.user)
        else:
            qs.data['has_new'] = False
        return qs
