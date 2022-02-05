from django.utils.translation import gettext_lazy as _
from django_elasticsearch_dsl_drf.constants import LOOKUP_QUERY_LT
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend, FilteringFilterBackend, SearchFilterBackend, \
    OrderingFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from organizations.serializers.query_param_serializers import OrganizationQueryParamSerializer
from search_indexes.documents.items import ShopItemDocument
from search_indexes.serializers.item import ShopItemsDocumentSerializer
from search_indexes.services.index_services import IndexServices
from search_indexes.services.transliteration import Transliteration
from shop.models import ShopItem
from shop.serializers.item_serializers import StartDateTimeSerializer
from shop.services.item_services import ShopItemService


class ShopItemDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer

    filter_backends = [
        FilteringFilterBackend,
        SearchFilterBackend,
        CompoundSearchFilterBackend,
        DefaultOrderingFilterBackend,
        OrderingFilterBackend
    ]

    pagination_class = GeneralPagination

    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'article': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'}
    }

    filter_fields = {
        'price': 'price.raw',
        'country': {
            'field': 'organization.country.code.raw'
        },
        'subcategories': {
            'field': 'subcategory.id',
        },
        'city': {
            'field': 'organization.city.id'
        },
        'category': {
            'field': 'subcategory.category.id',
        },
        'current_timestamp': {
            'field': 'updated_at',
            'lookups': [
                LOOKUP_QUERY_LT,
            ]
        },
    }

    ordering_fields = {
        'price': None,
        'updated_at': None
    }

    ordering = ('-updated_at',)

    def set_request_param(self, request, param, symbols):
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.query_params[param] = symbols
        request.query_params._mutable = mutable
        return super(ShopItemDocumentView, self).list(request)

    def list(self, request, *args, **kwargs):
        time = request.GET.get('current_timestamp_lt', None)
        if time:
            mutable = request.query_params._mutable
            request.query_params._mutable = True
            del request.GET['current_timestamp_lt']
            request.GET['current_timestamp__lt'] = time
            request.query_params._mutable = mutable

        search = request.GET.get('search', None)

        if search and search[0] == '#':  # Search among posts if hashtag is used
            qs = super(ShopItemDocumentView, self).list(request)
        else:
            qs = self.set_request_param(request, 'price__isnull', 'false')
        if search:
            # set reversed translate symbols (ggg --> ггг)
            translate_symbols = Transliteration.get_translit(search)

            # set reversed symbols (ggg --> ппп)
            reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(search))

            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.GET.appendlist('search', translate_symbols)
            request.GET.appendlist('search', reversed_symbols)
            request.query_params._mutable = mutable
            qs = super(ShopItemDocumentView, self).list(request)

        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        start_time = serializer.validated_data['start_time']
        if start_time:
            qs.data['has_new'] = ShopItemService.has_new(timestamp=start_time, user=request.user)
        else:
            qs.data['has_new'] = False
        return qs


class ShopOrgnizationItemDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer

    filter_backends = [
        FilteringFilterBackend,
        CompoundSearchFilterBackend,
        DefaultOrderingFilterBackend,
        OrderingFilterBackend
    ]

    pagination_class = GeneralPagination

    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'article': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'}
    }

    filter_fields = {
        'price': 'price.raw',
        'organization': {
            'field': 'organization.id.raw'
        },
        'country': {
            'field': 'organization.country.code.raw'
        },
        'subcategories': {
            'field': 'subcategory.id',
        },
        'category': {
            'field': 'subcategory.category.id',
        },
        'city': {
            'field': 'organization.city.id'
        },
    }

    ordering_fields = {
        'price': None,
        'updated_at': None,
    }

    ordering = ('-updated_at',)

    def set_request_param(self, request, param, symbols):
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.query_params[param] = symbols
        request.query_params._mutable = mutable
        return super(ShopOrgnizationItemDocumentView, self).list(request)

    def list(self, request, *args, **kwargs):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid organization is required in query parameters'))
        organization = serializer.validated_data['organization']
        if organization.is_deleted:
            raise NotAcceptableException(_('This organization is deleted'))

        search = request.GET.get('search', None)

        if search and search[0] == '#':  # Search among posts if hashtag is used
            qs = super(ShopOrgnizationItemDocumentView, self).list(request)
        else:
            qs = self.set_request_param(request, 'price__isnull', 'false')
        if search:
            # set reversed translate symbols (ggg --> ггг)
            translate_symbols = Transliteration.get_translit(search)

            # set reversed symbols (ggg --> ппп)
            reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(search))

            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.GET.appendlist('search', translate_symbols)
            request.GET.appendlist('search', reversed_symbols)
            request.query_params._mutable = mutable
            qs = super(ShopOrgnizationItemDocumentView, self).list(request)
        return qs
