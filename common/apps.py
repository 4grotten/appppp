from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'common'

    def ready(self):
        import common.signals
