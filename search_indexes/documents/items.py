from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import token_filter

from shop.models import ShopItem

# Name of the Elasticsearch index
INDEX = Index('items')
# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)


edge_ngram_completion_filter = token_filter(
    'edge_ngram_completion_filter',
    type="edge_ngram",
    min_gram=1,
    max_gram=20
)

edge_ngram_completion = analyzer(
    "edge_ngram_completion",
    tokenizer="standard",
    filter=["lowercase", edge_ngram_completion_filter]
)

html_strip = analyzer(
    'html_strip',
    tokenizer="whitespace",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)


@INDEX.doc_type
class ShopItemDocument(Document):
    id = fields.IntegerField(attr='id')
    article = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    created_at = fields.DateField()
    updated_at = fields.DateField()
    name = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField(),
        }
    )
    name_lang = fields.TextField()
    description = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField(),
        }
    )
    description_lang = fields.TextField()
    discount = fields.IntegerField()
    instagram_data = fields.ObjectField(
        properties={
            'thumbnail_url': fields.TextField(),
            'video_url': fields.TextField()
        }
    )
    instagram_link = fields.TextField()
    bookmarked_users = fields.TextField(
        attr='bookmarked_users_list',
        multi=True
    )
    liked_users = fields.TextField(
        attr='liked_users_list',
        multi=True
    )
    is_hidden = fields.BooleanField()
    subcategory = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name_ru': fields.TextField(),
            'name_en': fields.TextField(),
            'name_tr': fields.TextField(),
            'category': fields.ObjectField(
                properties={
                    'icon': fields.ObjectField(
                        properties={
                            'id': fields.IntegerField(),
                            'file': fields.FileField(),
                            'small': fields.TextField(attr='small_property'),
                            'medium': fields.TextField(attr='medium_property'),
                            'large': fields.TextField(attr='large_property'),
                            'name': fields.TextField(attr='name')
                        }
                    )
                }
            )
        }
    )
    images = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'file': fields.FileField(),
            'small': fields.TextField(attr='small_property'),
            'medium': fields.TextField(attr='medium_property'),
            'large': fields.TextField(attr='large_property'),
            'name': fields.TextField(attr='name')
        }
    )
    is_published = fields.BooleanField()
    is_updated = fields.BooleanField()
    price = fields.FloatField()
    removed_at = fields.DateField()
    youtube_links = fields.TextField()

    organization = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'currency': fields.ObjectField(
                properties={
                    'code': fields.TextField()
                }
            ),
            'image': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'file': fields.FileField(),
                    'small': fields.TextField(attr='small_property'),
                    'medium': fields.TextField(attr='medium_property'),
                    'large': fields.TextField(attr='large_property'),
                    'name': fields.TextField(attr='name')
                }
            ),
            'title': fields.TextField(),
            'phone_numbers': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'phone_number': fields.TextField()
                }
            ),
            'types': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'title_ru': fields.TextField(),
                    'title_en': fields.TextField(),
                    'title_tr': fields.TextField(),
                }
            )
        }
    )

    class Django(object):
        """Inner nested class Django."""
        model = ShopItem  # The model associate with this Document

