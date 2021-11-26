from django.apps import AppConfig


class SearchIndexesConfig(AppConfig):
    name = 'search_indexes'

    def ready(self):
        import search_indexes.signals
