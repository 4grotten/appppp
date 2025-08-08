import datetime
import logging
import random

from googletrans import Translator
from common.services.slack import bot_2
from instagram_parsers.services.proxy_services import ProxyService


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


class GoogleTranslator:
    @classmethod
    def get_translator(cls, text=None):
        proxy_str = ProxyService.get_random_formed_proxy()
        try:
            proxies = {"http": proxy_str, "https": proxy_str}
            user_agent = random.choice(USER_AGENTS)

            logging.info(f"Используется прокси {proxy_str} для перевода текста: {text}")
            translator = Translator(
                proxies=proxies,
                user_agent=user_agent,
                service_urls=["translate.googleapis.com"],
                raise_exception=True,
            )
            return translator

        except Exception as e:
            logging.error(
                f"Ошибка при создании переводчика с прокси {proxy_str}.\n"
                f"{e} \n"
                f"text: {text} \n"
                f"{datetime.datetime.now()}"
            )
            bot_2(f"Ошибка с переводчиком и прокси {proxy_str}:\n{e}\n{text}")
            try:
                translator = Translator(
                    service_urls=["translate.googleapis.com"],
                    user_agent=random.choice(USER_AGENTS),
                )
                return translator
            except Exception as e2:
                logging.error(
                    f"Ошибка при создании переводчика без прокси.\n{e2}\n{text}"
                )
                bot_2(f"Ошибка без прокси:\n{e2}\n{text}")
                return None

    @classmethod
    def translate(cls, text, lang):
        if len(text) > 5000:
            text = text[:5000]
        try:
            translator = cls.get_translator(text=text)
            if translator is None:
                return text
            result = translator.translate(text, dest=lang)
            return result.text
        except Exception as e:
            logging.error(f"Ошибка при переводе '{text}' -> '{lang}':\n{e}")
            bot_2(f"Ошибка перевода:\n{e}\n{text}")
            return text

    @classmethod
    def get_lang(cls, text):
        if len(text) > 100:
            text = text[:100]
        try:
            translator = cls.get_translator(text=text)
            if translator is None:
                return "en"
            detection = translator.detect(text)
            return detection.lang
        except Exception as e:
            bot_2(f"Ошибка определения языка:\n{e}\n{text}")
            return "en"
