from django.conf import settings
from django.db.models import Q
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl_drf.compat import KeywordField
from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import token_filter

from organizations.models import Organization

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])
# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=2,
)

edge_ngram_completion_filter = token_filter(
    'edge_ngram_completion_filter',
    type="edge_ngram",
    min_gram=1,
    max_gram=15,
)
edge_ngram_completion = analyzer(
    "edge_ngram_completion",
    type="custom",
    tokenizer="whitespace",
    filter=["lowercase", edge_ngram_completion_filter],
    char_filter=["html_strip"]
)
html_strip = analyzer(
    'html_strip',
    tokenizer="whitespace",
    filter=["lowercase"],
    char_filter=["html_strip"],
)

@INDEX.doc_type
class OrganizationDocument(Document):
    id = fields.IntegerField(attr='id')
    title = fields.TextField(
        analyzer=edge_ngram_completion,
        fields={
            'raw': KeywordField(),
            'suggest': fields.CompletionField(),
        }
    )
    promo_cashback = fields.FloatField()
    discounts = fields.ObjectField(
        properties={
            'percent': fields.IntegerField(),
        }
    )
    types = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'title_ru': fields.TextField(),
            'title_en': fields.TextField(),
            'title_tr': fields.TextField()
        }
    )
    image = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'file': fields.FileField(),
            'small': fields.TextField(attr='small_property'),
            'medium': fields.TextField(attr='medium_property'),
            'large': fields.TextField(attr='large_property'),
            'name': fields.TextField(attr='name')
        }
    )
    verification_status = fields.TextField()
    country = fields.ObjectField(
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
    )
    city = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
        }
    )

    def update(self, thing, refresh=None, action='index', **kwargs):
        if isinstance(thing, Organization) and not thing.is_active and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        if isinstance(thing, Organization) and thing.is_banned and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        if isinstance(thing, Organization) and thing.is_deleted and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        return super(OrganizationDocument, self).update(thing, refresh, action, **kwargs)

    def get_queryset(self):
        return super().get_queryset().exclude(
            Q(is_banned=True) | Q(is_deleted=True) | Q(is_active=False)
        )

    class Django(object):
        """Inner nested class Django."""
        model = Organization  # The model associate with this Document
