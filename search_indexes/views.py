from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from search_indexes.documents.items import ShopItemDocument
from search_indexes.serializers.item import ShopItemsDocumentSerializer
from search_indexes.services.index_services import IndexServices
from shop.models import ShopItem
from shop.serializers.item_serializers import StartDateTimeSerializer
from shop.services.item_services import ShopItemService


class ShopItemDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer
    pagination_class = GeneralPagination

    filter_backends = [DefaultOrderingFilterBackend,
                       CompoundSearchFilterBackend]

    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'article': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'}
    }

    ordering = ('_score',)

    # suggester_fields = {
    #     'name_suggest': {
    #         'field': 'name.suggest',
    #         'suggesters': [
    #             SUGGESTER_TERM,
    #             SUGGESTER_COMPLETION,
    #             SUGGESTER_PHRASE,
    #         ],
    #         'default_suggester': SUGGESTER_COMPLETION,
    #         'options': {
    #             'size': 10,  # Number of suggestions to retrieve.
    #             'skip_duplicates': True,  # Whether duplicate suggestions should be filtered out.
    #         },
    #     },
    #     'subcategory_suggest': {
    #         'field': 'subcategory.name.suggest',
    #         'suggesters': [
    #             SUGGESTER_TERM,
    #             SUGGESTER_COMPLETION,
    #             SUGGESTER_PHRASE,
    #         ],
    #     },
    #     'description_suggest': {
    #         'field': 'description.suggest',
    #         'suggesters': [
    #             SUGGESTER_TERM,
    #             SUGGESTER_COMPLETION,
    #             SUGGESTER_PHRASE,
    #         ],
    #     },
    # }

    def list(self, request, *args, **kwargs):
        qs = super(ShopItemDocumentView, self).list(request)

        symbols = request.query_params['search']
        reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(symbols))
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.query_params['search'] = reversed_symbols
        request.query_params._mutable = mutable

        qs_r = super(ShopItemDocumentView, self).list(request)

        qs = qs if qs.data['count'] > qs_r.data['count'] else qs_r
        return qs
