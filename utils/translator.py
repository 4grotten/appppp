import datetime
import logging

from googletrans import Translator
from httpx import URLLib3Transport, Proxy

from common.services.slack import bot_2
from instagram_parsers.services.proxy_services import ProxyService


class GoogleTranslator:

    @classmethod
    def get_translator(cls, text=None):
        random_proxy = (
            ProxyService.get_random_formed_proxy()
        )  # .replace("https://", '')
        try:
            proxies = {"https": URLLib3Transport(proxy=Proxy(random_proxy))}
            logging.info(
                f"используется прокси {random_proxy} для перевода текста: {text}"
            )
            translator = Translator(proxies=proxies)
            return translator
        except Exception as e:
            logging.error(
                f"Ошибка при создании переводчика с прокси {random_proxy}.\n"
                f"{e} \n"
                f"text: {text} \n"
                f"{datetime.datetime.now()}"
            )
            message = (
                f"Что то не так с переводчиком......\n"
                f"{e} \n"
                f"text: {text} \n"
                f"{datetime.datetime.now()}\n"
                f"прокси = {random_proxy}"
            )
            bot_2(message)
            try:
                translator = Translator()
                return translator
            except Exception as e:
                logging.error(
                    f"Ошибка при создании переводчика без прокси.\n"
                    f"{e} \n"
                    f"text: {text} \n"
                    f"{datetime.datetime.now()}"
                )
                message = (
                    f"Что то не так с переводчиком......\n"
                    f"{e} \n"
                    f"text: {text} \n"
                    f"{datetime.datetime.now()}\n"
                    f"прокси = {random_proxy}"
                )
                bot_2(message)
                return None

    @classmethod
    def translate(cls, text, lang):
        if len(text) > 100:
            text = text[0:5000]
        try:
            text = text.replace(".", " ")
            translator = cls.get_translator(text=text)
            logging.info(
                f"используется прокси {translator} для перевода текста: {text}"
            )
            if translator is None:
                return text
            translated_text = translator.translate(text, dest=lang)

            return translated_text
        except Exception as e:
            logging.error(
                f"Ошибка при переводе текста '{text}' на язык '{lang}'.\n"
                f"{e} \n"
                f"{datetime.datetime.now()}"
            )
            message = (
                f"Что то не так с переводчиком. Функция определения языка.\n"
                f"{e} \n"
                f"{datetime.datetime.now()}\n"
                f"text: {text}\n"
            )
            bot_2(message)
            return text

    @classmethod
    def get_lang(cls, text):
        if len(text) > 100:
            text = text[0:100]
        try:
            text = text.replace(".", " ")
            translator = cls.get_translator(text=text)
            if translator is None:
                return "en"
            detection = translator.detect(text)
            if isinstance(detection.lang, str):
                return detection.lang
            if isinstance(detection.lang, list):
                index = detection.confidence.index(max(detection.confidence))
                return detection.lang[index]
        except Exception as e:
            message = (
                f"Что то не так с переводчиком. Функция перевода текста.\n"
                f"{e} \n"
                f"{datetime.datetime.now()}\n"
                f"text: {text}\n"
            )
            bot_2(message)
            return "en"
