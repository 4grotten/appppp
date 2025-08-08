import datetime
import logging
import random
import time

from googletrans import Translator
from common.services.slack import bot_2
from instagram_parsers.services.proxy_services import ProxyService


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


class GoogleTranslator:
    MAX_RETRIES = 5

    @classmethod
    def _get_translator(cls, text=None):
        proxy_str = ProxyService.get_random_formed_proxy()
        if not proxy_str or not proxy_str.strip():
            proxy_str = None

        try:
            proxies = {"http": proxy_str, "https": proxy_str} if proxy_str else None
            user_agent = random.choice(USER_AGENTS)

            logging.info(f"Используется прокси {proxy_str} для перевода текста: {text}")
            translator = Translator(
                proxies=proxies,
                user_agent=user_agent,
                service_urls=[
                    "translate.google.com",
                    "translate.google.md",
                    "translate.google.me",
                    "translate.google.mg",
                    "translate.google.mk",
                    "translate.google.ml",
                    "translate.google.mn",
                    "translate.google.ms",
                    "translate.google.mu",
                    "translate.google.mv",
                    "translate.google.mw",
                    "translate.google.ne",
                    "translate.google.nf",
                    "translate.google.nl",
                    "translate.google.no",
                    "translate.google.nr",
                    "translate.google.nu",
                    "translate.google.pl",
                    "translate.google.pn",
                    "translate.google.ps",
                    "translate.google.pt",
                    "translate.google.ro",
                    "translate.google.rs",
                    "translate.google.ru",
                    "translate.google.rw",
                    "translate.google.sc",
                    "translate.google.se",
                    "translate.google.sh",
                    "translate.google.si",
                    "translate.google.sk",
                    "translate.google.sm",
                    "translate.google.sn",
                    "translate.google.so",
                    "translate.google.sr",
                    "translate.google.st",
                    "translate.google.td",
                    "translate.google.tg",
                ],
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

        last_exc = None
        for attempt in range(1, cls.MAX_RETRIES + 1):
            translator = cls._get_translator(text=text)
            if translator is None:
                break
            try:
                result = translator.translate(text, dest=lang)
                return result.text
            except Exception as e:
                last_exc = e
                logging.error(f"Ошибка при переводе попытка {attempt}: {e}")
                if "NoneType" in str(e) or "429" in str(e):
                    delay = random.uniform(2, 5)
                    logging.warning(f"Ошибка {e}, ждем {delay:.1f} сек и пробуем снова")
                    time.sleep(delay)
                else:
                    bot_2(f"Ошибка перевода:\n{e}\n{text}")
                    break
        logging.error(
            f"Не удалось перевести после {cls.MAX_RETRIES} попыток: {last_exc}"
        )
        return text

    @classmethod
    def get_lang(cls, text):
        if not text:
            return "en"

        text = text.replace(".", " ").strip()
        if len(text) > 100:
            text = text[:100]

        translator = cls._get_translator(text=text)
        if not translator:
            return "en"

        try:
            detection = translator.detect(text)
            if isinstance(detection.lang, str):
                return detection.lang
            if isinstance(detection.lang, list):
                idx = detection.confidence.index(max(detection.confidence))
                return detection.lang[idx]
        except Exception as e:
            bot_2(f"Ошибка определения языка: {e}\ntext: {text}")
            return "en"
