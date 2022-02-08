from django_elasticsearch_dsl_drf.constants import LOOKUP_FILTER_PREFIX, \
    LOOKUP_FILTER_RANGE, LOOKUP_QUERY_IN, LOOKUP_FILTER_TERMS, LOOKUP_FILTER_WILDCARD, \
    LOOKUP_QUERY_EXCLUDE
from django_elasticsearch_dsl_drf.filter_backends import \
    DefaultOrderingFilterBackend, FilteringFilterBackend, MultiMatchSearchFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from common.pagination import GeneralPagination
from search_indexes.documents.organizations import OrganizationDocument
from search_indexes.serializers.organization import OrganizationIndexSerializer


class OrganizationDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = OrganizationDocument
    serializer_class = OrganizationIndexSerializer

    filter_backends = [
        FilteringFilterBackend,
        # CompoundSearchFilterBackend,
        # SearchFilterBackend,
        DefaultOrderingFilterBackend,
        MultiMatchSearchFilterBackend,
        # MultiMatchQueryBackend
    ]
    pagination_class = GeneralPagination

    # search_fields = {
    #     'title': {'fuzziness': 'AUTO'},
    # }

    multi_match_search_fields = (
        'title'
    )

    # multi_match_options = {'operator': 'and'}

    filter_fields = {
        'country': {
            'field': 'country.code.raw'
        },
        'city': {
            'field': 'city.id'
        }
    }

    def list(self, request, *args, **kwargs):
        search = request.GET.get('search', None)

        if search:
            # set reversed translate symbols (ggg --> ггг)
            # translate_symbols = Transliteration.get_translit(search)

            # set reversed symbols (ggg --> ппп)
            # reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(search))
            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.GET['search_multi_match'] = search
            # request.GET.appendlist('search_multi_match', reversed_symbols)
            # request.GET.appendlist('search_multi_match', translate_symbols)
            del request.GET['search']
            request.query_params._mutable = mutable
            qs = super(OrganizationDocumentView, self).list(request)
        else:
            qs = super(OrganizationDocumentView, self).list(request)
        return qs
