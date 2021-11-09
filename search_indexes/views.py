from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

# Example app models
from search_indexes.documents.items import ShopItemDocument
from search_indexes.serializers.item import ShopItemsDocumentSerializer


class ShopItemDocumentView(DocumentViewSet):
    """The PublisherDocument view."""
    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer

    filter_backends = [CompoundSearchFilterBackend]

    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'},
    }

    # multi_match_search_fields = {
    #     'name': {'boost': 2},
    #     'description': None,
    # }
