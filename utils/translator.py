import datetime

from googletrans import Translator
from httpx import URLLib3Transport, Proxy

from common.exceptions import IntegrityException
from common.services.slack import bot
from instagram_parsers.services.proxy_services import ProxyService


class GoogleTranslator:

    def __init__(self):
        self.random_proxy = ProxyService.get_random_formed_proxy()  #.replace("https://", '')
        try:
            self.proxies = {'https': URLLib3Transport(proxy=Proxy(self.random_proxy))}
            self.translator = Translator(proxies=self.proxies)
        except AttributeError as e:
            message = f"Что то не так с переводчиком......\n" \
                      f"{e} \n" \
                      f"{datetime.datetime.now()}\n" \
                      f"прокси = {self.random_proxy}"
            bot(message)
            self.translator = Translator()

    def translate(self, text, lang):
        if len(text) > 100:
            text = text[0:5000]
        try:
            text = text.replace('.', " ")
            translated_text = self.translator.translate(text, dest=lang)
            return translated_text
        except Exception as e:
            raise IntegrityException('Could not Translate - {world}: {e}'.format(e=str(e), world=text))

    def get_lang(self, text):
        if len(text) > 100:
            text = text[0:100]
        try:
            text = text.replace('.', " ")
            detection = self.translator.detect(text)
            if isinstance(detection.lang, str):
                return detection.lang
            if isinstance(detection.lang, list):
                index = detection.confidence.index(max(detection.confidence))
                return detection.lang[index]
        except Exception as e:
            raise IntegrityException('Could not define languish: {e}'.format(e=str(e)))
