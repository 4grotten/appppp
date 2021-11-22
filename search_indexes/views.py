import re

from django_elasticsearch_dsl_drf.constants import SUGGESTER_COMPLETION, SUGGESTER_TERM, SUGGESTER_PHRASE
from django_elasticsearch_dsl_drf.filter_backends import \
    CompoundSearchFilterBackend, SuggesterFilterBackend
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

# Example app models
from search_indexes.documents.items import ShopItemDocument
from search_indexes.serializers.item import ShopItemsDocumentSerializer


class ShopItemDocumentView(DocumentViewSet):
    """The ShopItemDocument view."""

    document = ShopItemDocument
    serializer_class = ShopItemsDocumentSerializer

    filter_backends = [CompoundSearchFilterBackend, SuggesterFilterBackend]

    search_fields = {
        'name': {'fuzziness': 'AUTO'},
        'article': {'fuzziness': 'AUTO'},
        'description': {'fuzziness': 'AUTO'}
    }

    suggester_fields = {
        'name_suggest': {
            'field': 'name.suggest',
            'suggesters': [
                SUGGESTER_TERM,
                SUGGESTER_COMPLETION,
                SUGGESTER_PHRASE,
            ],
            'default_suggester': SUGGESTER_COMPLETION,
            'options': {
                'size': 10,  # Number of suggestions to retrieve.
                'skip_duplicates': True,  # Whether duplicate suggestions should be filtered out.
            },
        },
        'subcategory_suggest': {
            'field': 'subcategory.name.suggest',
            'suggesters': [
                SUGGESTER_TERM,
                SUGGESTER_COMPLETION,
                SUGGESTER_PHRASE,
            ],
        },
        'description_suggest': {
            'field': 'description.suggest',
            'suggesters': [
                SUGGESTER_TERM,
                SUGGESTER_COMPLETION,
                SUGGESTER_PHRASE,
            ],
        },
    }

    def list(self, request, *args, **kwargs):
        qs = super(ShopItemDocumentView, self).list(request)

        symbols = request.query_params['search']
        reversed_symbols = self.change_layout(self.remove_bad_char(symbols))
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.query_params['search'] = reversed_symbols
        request.query_params._mutable = mutable
        qs_r = super(ShopItemDocumentView, self).list(request)

        qs = qs if qs.data['count'] > qs_r.data['count'] else qs_r
        return qs

    @staticmethod
    def remove_bad_char(symbols: str):
        symbols = symbols.replace('ё', 'е')
        symbols = symbols.replace('Ё', 'Е')
        return symbols

    @staticmethod
    def change_layout(string: str):
        char_map = (
            ("a", "ф"), ("c", "с"), ("d", "в"), ("e", "у"), ("b", "и"), ("f", "а"), ("g", "п"), ("h", "р"), ("i", "ш"),
            ("j", "о"), ("k", "л"), ("l", "д"),
            ("m", "ь"), ("n", "т"), ("o", "щ"), ("p", "з"), ("r", "к"), ("s", "ы"), ("t", "е"), ("u", "г"), ("v", "м"),
            ("w", "ц"), ("x", "ч"), ("y", "н"),
            ("z", "я"), ("A", "Ф"), ("B", "И"), ("C", "С"), ("D", "В"), ("E", "У"), ("F", "А"), ("G", "П"), ("H", "Р"),
            ("I", "Ш"), ("J", "О"), ("K", "Л"),
            ("L", "Д"), ("M", "Ь"), ("N", "Т"), ("O", "Щ"), ("P", "З"), ("R", "К"), ("S", "Ы"), ("T", "Е"), ("U", "Г"),
            ("V", "М"), ("W", "Ц"), ("X", "Ч"),
            ("Y", "Н"), ("Z", "Я"), ("[", "х"), ("]", "ъ"), (";", "ж"), ("<", "б"), (">", "ю"), ("й", "q"), ("Й", "Q")
        )
        re_forbidden_chars = re.compile(r"[\]\[<>]")
        invert_str, invert_str_list = '', []
        for char in string:
            char_ready = False
            for match in char_map:
                if char == match[0]:
                    invert_str_list.append(match[1])
                    char_ready = True
                elif char == match[1]:
                    if re_forbidden_chars.match(match[0]):
                        # ignore some chars
                        invert_str_list.append(char)
                    else:
                        invert_str_list.append(match[0])
                        char_ready = True
            if not char_ready:
                invert_str_list.append(char)
        return "".join(invert_str_list)

