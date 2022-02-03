from django.utils.translation import gettext_lazy as _
from django_elasticsearch_dsl_drf.constants import LOOKUP_QUERY_LT, LOOKUP_FILTER_WILDCARD, LOOKUP_FILTER_PREFIX, \
    LOOKUP_FILTER_TERMS, LOOKUP_QUERY_IN, LOOKUP_QUERY_EXCLUDE, LOOKUP_QUERY_CONTAINS, LOOKUP_FILTER_FUZZY, \
    FUNCTIONAL_SUGGESTER_COMPLETION_MATCH
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend, FilteringFilterBackend, SearchFilterBackend, \
    OrderingFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from search_indexes.documents.organizations import OrganizationDocument
from search_indexes.serializers.organization import OrganizationIndexSerializer
from search_indexes.services.index_services import IndexServices
from search_indexes.services.transliteration import Transliteration


class OrganizationDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = OrganizationDocument
    serializer_class = OrganizationIndexSerializer

    filter_backends = [
        FilteringFilterBackend,
        SearchFilterBackend,
        CompoundSearchFilterBackend,
        DefaultOrderingFilterBackend,
        # OrderingFilterBackend
    ]

    pagination_class = GeneralPagination

    search_fields = {
        'title': {'fuzziness': 'AUTO'}
    }

    filter_fields = {
        'country': {
            'field': 'country.code.raw'
        },
        'city': {
            'field': 'city.id'
        },
        'title': {
            'field': 'title',
            'lookups': [
                LOOKUP_FILTER_FUZZY,
                LOOKUP_FILTER_PREFIX
            ],
        },
    }

    # ordering = ('title.raw',)

    def list(self, request, *args, **kwargs):
        search = request.GET.get('search', None)
        print(request.query_params)
        if search:
            # set reversed translate symbols (ggg --> ггг)
            translate_symbols = Transliteration.get_translit(search)

            # set reversed symbols (ggg --> ппп)
            reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(search))

            mutable = request.query_params._mutable
            request.query_params._mutable = True
            # request.GET['title__prefix'] = search
            request.GET.appendlist('search', translate_symbols)
            request.GET.appendlist('search', reversed_symbols)
            # del request.GET['search']
            # request.GET.appendlist('search', translate_symbols)
            # request.GET.appendlist('search', reversed_symbols)
            request.query_params._mutable = mutable
            print(request.query_params)
            qs = super(OrganizationDocumentView, self).list(request)
        else:
            qs = super(OrganizationDocumentView, self).list(request)
        return qs
