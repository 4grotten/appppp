from googletrans import Translator
from httpx import URLLib3Transport, Proxy

from instagram_parsers.services.proxy_services import ProxyService


class GoogleTranslator:

    def __init__(self):
        self.random_proxy = ProxyService.get_random_formed_proxy(True)  #.replace("https://", '')
        self.proxies = {'http': URLLib3Transport(proxy=Proxy(self.random_proxy))}
        self.translator = Translator(proxies=self.proxies)

    def translate(self, text, lang):
        translated_text = self.translator.translate(text, dest=lang)
        return translated_text

    def get_lang(self, text):
        detection = self.translator.detect(text)
        if isinstance(detection.lang, str):
            return detection.lang
        if isinstance(detection.lang, list):
            index = detection.confidence.index(max(detection.confidence))
            return detection.lang[index]
