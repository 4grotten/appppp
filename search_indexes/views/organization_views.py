from django_elasticsearch_dsl_drf.constants import LOOKUP_FILTER_PREFIX, \
    LOOKUP_FILTER_FUZZY
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend, FilteringFilterBackend, SearchFilterBackend
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
        CompoundSearchFilterBackend,
        DefaultOrderingFilterBackend,
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
        }
    }

    def list(self, request, *args, **kwargs):
        search = request.GET.get('search', None)
        if search:
            # set reversed translate symbols (ggg --> ггг)
            translate_symbols = Transliteration.get_translit(search)

            # set reversed symbols (ggg --> ппп)
            reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(search))

            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.GET.appendlist('search', reversed_symbols)
            request.GET.appendlist('search', translate_symbols)
            request.query_params._mutable = mutable
            qs = super(OrganizationDocumentView, self).list(request)
        else:
            qs = super(OrganizationDocumentView, self).list(request)
        return qs
