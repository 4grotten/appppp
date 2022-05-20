from django_elasticsearch_dsl_drf.filter_backends import \
    FilteringFilterBackend, DefaultOrderingFilterBackend, MultiMatchSearchFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from search_indexes.documents.items import SuggestDocument
from search_indexes.serializers.item import SuggestDocumentSerializer


# class ShopItemDocumentView(DocumentViewSet):
#     """The ShopItemDocument view."""
#
#     document = ShopItemDocument
#     serializer_class = ShopItemsDocumentSerializer
#
#     filter_backends = [
#         FilteringFilterBackend,
#         DefaultOrderingFilterBackend,
#         OrderingFilterBackend,
#         MultiMatchSearchFilterBackend
#     ]
#
#     pagination_class = GeneralPagination
#
#     multi_match_search_fields = (
#         'name', 'article', 'description'
#     )
#
#     multi_match_options = {
#         'type': 'phrase_prefix'
#     }
#
#     filter_fields = {
#         'price': 'price.raw',
#         'country': {
#             'field': 'organization.country.code.raw'
#         },
#         'subcategories': {
#             'field': 'subcategory.id',
#         },
#         'city': {
#             'field': 'organization.city.id'
#         },
#         'category': {
#             'field': 'subcategory.category.id',
#         },
#         'current_timestamp': {
#             'field': 'updated_at',
#             'lookups': [
#                 LOOKUP_QUERY_LT,
#             ]
#         },
#         'is_private': {
#             'field': 'organization.is_private',
#         },
#     }
#
#     ordering_fields = {
#         'price': None,
#         'updated_at': None
#     }
#
#     ordering = ('-updated_at',)
#
#     def set_request_param(self, request, param, symbols):
#         mutable = request.query_params._mutable
#         request.query_params._mutable = True
#         request.query_params[param] = symbols
#         request.query_params._mutable = mutable
#         return super(ShopItemDocumentView, self).list(request)
#
#     def list(self, request, *args, **kwargs):
#         time = request.GET.get('current_timestamp_lt', None)
#         subcategories = request.GET.get('subcategories', None)
#         if subcategories:
#             array = subcategories.split(',')
#             mutable = request.query_params._mutable
#             request.query_params._mutable = True
#             del request.GET['subcategories']
#             request.GET.setlist('subcategories', array)
#             request.query_params._mutable = mutable
#
#         if time:
#             mutable = request.query_params._mutable
#             request.query_params._mutable = True
#             del request.GET['current_timestamp_lt']
#             request.GET['current_timestamp__lt'] = time
#             request.query_params._mutable = mutable
#
#         search = request.GET.get('search', None)
#
#         if search and search[0] == '#':  # Search among posts if hashtag is used
#             qs = super(ShopItemDocumentView, self).list(request)
#         else:
#             self.set_request_param(request, 'price__isnull', 'false')
#             qs = self.set_request_param(request, 'is_private', 'false')
#
#         if search:
#             mutable = request.query_params._mutable
#             request.query_params._mutable = True
#             request.GET['search_multi_match'] = search
#             del request.GET['search']
#             request.query_params._mutable = mutable
#             qs = super(ShopItemDocumentView, self).list(request)
#
#         serializer = StartDateTimeSerializer(data=request.GET)
#         if not serializer.is_valid():
#             raise NotAcceptableException(_('Validation Error'))
#         start_time = serializer.validated_data['start_time']
#         if start_time:
#             qs.data['has_new'] = ShopItemService.feed_has_new_items(timestamp=start_time)
#         else:
#             qs.data['has_new'] = False
#         return qs
#
#
# class ShopOrgnizationItemDocumentView(DocumentViewSet):
#     """The ShopItemDocument view."""
#
#     document = ShopItemDocument
#     serializer_class = ShopItemsDocumentSerializer
#
#     filter_backends = [
#         FilteringFilterBackend,
#         DefaultOrderingFilterBackend,
#         OrderingFilterBackend,
#         MultiMatchSearchFilterBackend
#     ]
#
#     pagination_class = GeneralPagination
#
#     multi_match_search_fields = (
#         'name', 'article', 'description'
#     )
#
#     multi_match_options = {
#         'type': 'phrase_prefix'
#     }
#
#     filter_fields = {
#         'price': 'price.raw',
#         'organization': {
#             'field': 'organization.id.raw'
#         },
#         'country': {
#             'field': 'organization.country.code.raw'
#         },
#         'subcategories': {
#             'field': 'subcategory.id',
#         },
#         'category': {
#             'field': 'subcategory.category.id',
#         },
#         'city': {
#             'field': 'organization.city.id'
#         },
#     }
#
#     ordering_fields = {
#         'price': None,
#         'updated_at': None,
#     }
#
#     ordering = ('-updated_at',)
#
#     def set_request_param(self, request, param, symbols):
#         mutable = request.query_params._mutable
#         request.query_params._mutable = True
#         request.query_params[param] = symbols
#         request.query_params._mutable = mutable
#         return super(ShopOrgnizationItemDocumentView, self).list(request)
#
#     def list(self, request, *args, **kwargs):
#         organization = OrganizationService.get(id=request.GET.get('organization', None))
#
#         if request.user.is_authenticated is False and organization.is_private is True:
#             return Response(data={
#                 'message': _('This organization is private'),
#             }, status=status.HTTP_406_NOT_ACCEPTABLE)
#
#         if request.user.is_authenticated and not OrganizationService.user_can_edit_organization(user=request.user,
#                                                                                                 organization=organization) \
#                 and organization.is_private is True \
#                 and SubscriptionService.is_subscribed(user=request.user, organization=organization) != 'subscribed':
#             return Response(data={
#                 'message': _('This organization is private for you, need to subscribe'),
#             }, status=status.HTTP_406_NOT_ACCEPTABLE)
#
#         serializer = OrganizationQueryParamSerializer(data=self.request.GET)
#         if not serializer.is_valid():
#             raise NotAcceptableException(_('Valid organization is required in query parameters'))
#         organization = serializer.validated_data['organization']
#         if organization.is_deleted:
#             raise NotAcceptableException(_('This organization is deleted'))
#         search = request.GET.get('search', None)
#         if search and search[0] == '#':  # Search among posts if hashtag is used
#             qs = super(ShopOrgnizationItemDocumentView, self).list(request)
#         else:
#             qs = super(ShopOrgnizationItemDocumentView, self).list(request)
#         if search:
#             # set reversed translate symbols (ggg --> ггг)
#             # translate_symbols = Transliteration.get_translit(search)
#
#             # set reversed symbols (ggg --> ппп)
#             # reversed_symbols = IndexServices.change_layout(IndexServices.remove_bad_char(search))
#
#             mutable = request.query_params._mutable
#             request.query_params._mutable = True
#             request.GET['search_multi_match'] = search
#             # request.GET.appendlist('search_multi_match', translate_symbols)
#             # request.GET.appendlist('search_multi_match', reversed_symbols)
#             del request.GET['search']
#             request.query_params._mutable = mutable
#             qs = super(ShopOrgnizationItemDocumentView, self).list(request)
#         serializer = StartDateTimeSerializer(data=request.GET)
#         if not serializer.is_valid():
#             raise NotAcceptableException(_('Validation Error'))
#         start_time = serializer.validated_data['start_time']
#         if start_time:
#             qs.data['has_new'] = ShopItemService.subscription_has_new_items(timestamp=start_time, user=request.user)
#         else:
#             qs.data['has_new'] = False
#         return qs


# class SuggestSearchDocumentView(DocumentViewSet):
#     """The ShopItemDocument view."""
#     document = SuggestDocument
#     serializer_class = SuggestDocumentSerializer
#
#     filter_backends = [
#         SuggesterFilterBackend,
#     ]
#
#     suggester_fields = {
#         'name_suggest_context': {
#             'field': 'name.suggest_context',
#             'default_suggester': [
#                 SUGGESTER_COMPLETION,
#             ],
#             'completion_options': {
#                 'category_filters': {
#                     'name_suggest_code': 'code',
#                     'name_suggest_name_lang': 'name_lang',
#                 }
#             },
#             'options': {
#                 'size': 10,  # Override default number of suggestions
#                 'skip_duplicates': True,  # Whether duplicate suggestions should be filtered out.
#             },
#         },
#     }


# class SuggestSearchDocumentView(DocumentViewSet):
#     """The ShopItemDocument view."""
#     document = SuggestDocument
#     serializer_class = SuggestDocumentSerializer
#
#     filter_backends = [
#         SuggesterFilterBackend,
#     ]
#
#     suggester_fields = {
#         'name_suggest': {
#             'field': 'name.suggest',
#             'default_suggester': [SUGGESTER_COMPLETION, ],
#         },
#         'name_suggest_context': {
#             'field': 'name.suggest_context',
#             'default_suggester': [SUGGESTER_COMPLETION, ],
#             'completion_options': {
#                 'filters': {
#                     'name_suggest_code': 'code',
#                     'name_suggest_name_lang': 'name_lang',
#                     'size': 10,
#                 },
#             }
#         }
#     }

# suggester_fields = {
#     'name_suggest_context': {
#         'field': 'name.suggest_context',
#         'default_suggester': [
#             SUGGESTER_COMPLETION,
#         ],
#         'completion_options': {
#             'category_filters': {
#                 'name_suggest_code': 'code',
#                 'name_suggest_name_lang': 'name_lang',
#             }
#         },
#         'options': {
#             'size': 10,  # Override default number of suggestions
#             'skip_duplicates': True,  # Whether duplicate suggestions should be filtered out.
#         },
#     },
# }


class SuggestSearchDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = SuggestDocument
    serializer_class = SuggestDocumentSerializer

    filter_backends = [
        FilteringFilterBackend,
        DefaultOrderingFilterBackend,
        MultiMatchSearchFilterBackend
    ]

    # pagination_class = GeneralPagination

    multi_match_search_fields = (
        'name',
    )

    multi_match_options = {
        'type': 'phrase_prefix'
    }

    filter_fields = {
        'country': {
            'field': 'organization.country.code.raw'
        },
        'price': 'price.raw',
        'is_private': {
            'field': 'organization.is_private',
        },
    }

    ordering = ('name.raw',)

    def set_request_param(self, request, param, symbols):
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.query_params[param] = symbols
        request.query_params._mutable = mutable
        return super(SuggestSearchDocumentView, self).list(request)

    def list(self, request, *args, **kwargs):

        search = request.GET.get('suggest_items', None)

        if search and search[0] == '#':  # Search among posts if hashtag is used
            qs = super(SuggestSearchDocumentView, self).list(request)
        else:
            self.set_request_param(request, 'price__isnull', 'false')
            qs = self.set_request_param(request, 'is_private', 'false')

        if search:
            mutable = request.query_params._mutable
            request.query_params._mutable = True
            request.GET['search_multi_match'] = search
            del request.GET['suggest_items']
            request.query_params._mutable = mutable
            qs = super(SuggestSearchDocumentView, self).list(request)
        array_items = []
        pop_index = []
        limit_of_items = 20
        for i in range(len(qs.data.get('results'))):
            if qs.data.get('results')[i].get('name') not in array_items and qs.data.get('results')[i].get(
                    'name').lower().startswith(search.lower()) == True and i <= limit_of_items:
                array_items.append(qs.data.get('results')[i].get('name'))
            else:
                pop_index.append(i)
        for i in range(len(qs.data.get('results')) - 1, -1, -1):
            if i in pop_index:
                qs.data.get('results').pop(i)
        qs.data['count'] = len(array_items)
        del qs.data['facets']
        del qs.data['previous']
        del qs.data['next']
        return qs
