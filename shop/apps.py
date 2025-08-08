from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = "shop"

    def ready(self):
        from googletrans import Translator

        if not hasattr(Translator, "raise_Exception"):

            def raise_Exception(self, *args, **kwargs):
                if getattr(self, "raise_exception", False):
                    raise Exception("Translation failed")
                return None

            Translator.raise_Exception = raise_Exception
