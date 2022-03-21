from django_elasticsearch_dsl_drf.constants import LOOKUP_QUERY_CONTAINS
from django_elasticsearch_dsl_drf.filter_backends import \
    DefaultOrderingFilterBackend, FilteringFilterBackend, CompoundSearchFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

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
        # CompoundSearchFilterBackend,
        # SearchFilterBackend,
        DefaultOrderingFilterBackend,
        # MultiMatchSearchFilterBackend,
        # MultiMatchQueryBackend
    ]
    pagination_class = GeneralPagination

    # search_fields = {
    #     'title': {'fuzziness': 'AUTO'},
    # }

    # multi_match_search_fields = (
    #     'title'
    # )

    # multi_match_options = {'operator': 'and'}

    filter_fields = {
        'country': {
            'field': 'country.code.raw'
        },
        'city': {
            'field': 'city.id',
        },
        'name': {
            'field': 'title',
            'lookups': [
                LOOKUP_QUERY_CONTAINS,
            ],
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
            search = search.lower()
            request.GET['name__contains'] = search
            # request.GET.appendlist('name__contains', reversed_symbols)
            # request.GET.appendlist('name__contains', translate_symbols)
            del request.GET['search']
            request.query_params._mutable = mutable
            qs = super(OrganizationDocumentView, self).list(request)
        else:
            qs = super(OrganizationDocumentView, self).list(request)
        return qs
