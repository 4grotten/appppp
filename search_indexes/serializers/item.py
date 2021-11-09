from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from search_indexes.documents.items import ShopItemDocument


class ShopItemsDocumentSerializer(DocumentSerializer):

    class Meta:
        document = ShopItemDocument
        fields = ('id', 'name', 'description',)
