from django.utils.translation import gettext_lazy as _
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend, FilteringFilterBackend, SuggesterFilterBackend, \
    SearchFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from search_indexes.documents.items import ShopItemDocument
from search_indexes.serializers.item import ShopItemsDocumentSerializer
from search_indexes.services.index_services import IndexServices
from search_indexes.services.transliteration import Transliteration
from shop.serializers.item_serializers import StartDateTimeSerializer
from shop.services.item_services import ShopItemService


class ShopItemDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer

    filter_backends = [
        FilteringFilterBackend,
        SearchFilterBackend,
        DefaultOrderingFilterBackend,
        CompoundSearchFilterBackend,
        SuggesterFilterBackend,
    ]
    pagination_class = GeneralPagination
    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'article': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'}
    }

    # search_fields = (
    #     'name',
    #     'article',
    #     'description'
    # )

    filter_fields = {
        'price': 'price.raw',
        'country_code': 'organization.country.code.raw',
        'subcategories': {
            'field': 'subcategory.id',
        },
        'city': {
            'field': 'organization.city.id'
        },
    }

    def set_request_param(self, request, param, symbols):
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.query_params[param] = symbols
        request.query_params._mutable = mutable
        return super(ShopItemDocumentView, self).list(request)

    def list(self, request, *args, **kwargs):
        search = request.GET.get('search', None)

        if search and search[0] == '#':  # Search among posts if hashtag is used
            qs = super(ShopItemDocumentView, self).list(request)
        else:
            qs = self.set_request_param(request, 'price__isnull', 'false')

        if search:
            symbols = request.query_params['search']

            # set reversed symbols
            reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(symbols))
            qs_r = self.set_request_param(request, 'search', reversed_symbols)

            # set translate symbols
            translate_symbols = Transliteration.get_translit(symbols)
            qt_r = self.set_request_param(request, 'search', translate_symbols)

            if qs.data['total_count'] >= qs_r.data['total_count'] and qs.data['total_count'] >= \
                    qt_r.data['total_count']:
                qs = qs
            elif qs_r.data['total_count'] > qs.data['total_count'] and qs_r.data['total_count'] > \
                    qt_r.data['total_count']:
                qs = qs_r
            else:
                qs = qt_r

        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        start_time = serializer.validated_data['start_time']
        if start_time:
            qs.data['has_new'] = ShopItemService.has_new(timestamp=start_time, user=request.user)
        else:
            qs.data['has_new'] = False
        return qs
