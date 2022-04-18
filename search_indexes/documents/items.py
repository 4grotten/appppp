from django.conf import settings

from django.db.models import Q
from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import token_filter
from django_elasticsearch_dsl_drf.compat import KeywordField
from shop.models import ShopItem

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])
# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=5,
    number_of_replicas=2,
)

edge_ngram_completion_filter = token_filter(
    'edge_ngram_completion_filter',
    type="edge_ngram",
    min_gram=2,
    max_gram=15,
)
edge_ngram_completion = analyzer(
    "edge_ngram_completion",
    type="custom",
    tokenizer="whitespace",
    filter=["lowercase", edge_ngram_completion_filter, "snowball"],
    char_filter=["html_strip"]
)

html_strip = analyzer(
    'html_strip',
    tokenizer="whitespace",
    filter=["lowercase"],
    char_filter=["html_strip"],
)


@INDEX.doc_type
class ShopItemDocument(Document):
    id = fields.IntegerField(attr='id')
    article = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField(),

        }
    )
    name = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField(),
        }
    )
    description = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.KeywordField(ignore_above=10000),
            'suggest': fields.CompletionField(),
        }
    )
    price = fields.FloatField(
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    is_published = fields.BooleanField()
    is_updated = fields.BooleanField()
    removed_at = fields.DateField()
    youtube_links = fields.TextField()
    name_lang = fields.TextField()
    created_at = fields.DateField()
    updated_at = fields.DateField()
    description_lang = fields.TextField()
    discount = fields.IntegerField()
    instagram_link = fields.TextField()
    is_hidden = fields.BooleanField()

    instagram_data = fields.ObjectField(
        properties={
            'thumbnail_url': fields.TextField(),
            'video_url': fields.TextField()
        }
    )

    bookmarked_users = fields.TextField(
        attr='bookmarked_users_list',
        multi=True
    )

    liked_users = fields.TextField(
        attr='liked_users_list',
        multi=True
    )

    comments = fields.TextField(
        attr='comment_count_list',
        multi=True
    )

    subcategory = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name_ru': fields.TextField(),
            'name_en': fields.TextField(),
            'name_tr': fields.TextField(),
            'category': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
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

    videos = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'video': fields.FileField(),
            'video_url': fields.TextField(),
            'thumbnail': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'file': fields.FileField(),
                    'small': fields.TextField(attr='small_property'),
                    'medium': fields.TextField(attr='medium_property'),
                    'large': fields.TextField(attr='large_property'),
                    'name': fields.TextField(attr='name')
                }
            ),
            'name': fields.TextField(attr='name')
        }
    )

    organization = fields.ObjectField(
        properties={
            'id': fields.IntegerField(
                fields={
                    'raw': KeywordField(),
                }
            ),
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
            'country': fields.ObjectField(
                properties={
                    'code': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': KeywordField(),
                            'suggest': fields.CompletionField(),
                        }
                    ),
                    'name': fields.TextField(),
                }
            ),
            'city': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'name': fields.TextField(),
                }
            ),
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
                    'title_tr': fields.TextField()
                }
            ),
            'verification_status': fields.TextField(),
            'is_private': fields.BooleanField(),
        }
    )

    def update(self, thing, refresh=None, action='index', **kwargs):
        if isinstance(thing, ShopItem) and not thing.is_published and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        if isinstance(thing, ShopItem) and thing.organization.is_banned and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        if isinstance(thing, ShopItem) and thing.organization.is_deleted and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        return super(ShopItemDocument, self).update(thing, refresh, action, **kwargs)

    def get_queryset(self):
        return super().get_queryset().exclude(
            Q(organization__is_banned=True) | Q(organization__is_deleted=True) | Q(is_published=False)
        )

    class Django(object):
        """Inner nested class Django."""
        model = ShopItem  # The model associate with this Document
