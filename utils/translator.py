import datetime
import logging
import random
import time

from googletrans import Translator
from common.services.slack import bot_2
from instagram_parsers.services.proxy_services import ProxyService


class GoogleTranslator:
    MAX_TEXT_LEN = 5000
    RETRY_COUNT = 5

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0",
    ]

    @classmethod
    def _get_translator(cls, text=None):
        """Создаёт переводчик с прокси или без него."""
        random_proxy = ProxyService.get_random_formed_proxy()
        try:
            translator = Translator()
            # Меняем сессию после создания
            translator.session.proxies = {
                "http": random_proxy,
                "https": random_proxy,
            }
            translator.session.headers.update(
                {"User-Agent": random.choice(cls.USER_AGENTS)}
            )
            logging.info(
                f"[Translator] Используется прокси {random_proxy} для текста: {text}"
            )
            return translator
        except Exception as e:
            logging.error(
                f"Ошибка при создании переводчика с прокси {random_proxy}.\n"
                f"{e}\ntext: {text}\n{datetime.datetime.now()}"
            )
            bot_2(
                f"Проблема с переводчиком через прокси {random_proxy}\n{e}\ntext: {text}"
            )
            try:
                translator = Translator()
                translator.session.headers.update(
                    {"User-Agent": random.choice(cls.USER_AGENTS)}
                )
                logging.info("[Translator] Пробую без прокси...")
                return translator
            except Exception as e2:
                logging.error(f"Ошибка без прокси: {e2}")
                bot_2(f"Переводчик умер даже без прокси.\n{e2}")
                return None

    @classmethod
    def translate(cls, text, lang):
        if not text:
            return None

        text = text.replace(".", " ").strip()
        if len(text) > cls.MAX_TEXT_LEN:
            text = text[: cls.MAX_TEXT_LEN]

        for attempt in range(1, cls.RETRY_COUNT + 1):
            translator = cls._get_translator(text=text)
            if not translator:
                return text

            try:
                result = translator.translate(text, dest=lang)
                if hasattr(result, "text"):
                    return result
                return text
            except Exception as e:
                err_str = str(e)
                logging.error(f"[Translator] Ошибка на попытке {attempt}: {err_str}")
                if "429" in err_str:
                    delay = random.uniform(3, 8) * attempt
                    logging.warning(
                        f"[Translator] Поймал 429, жду {delay:.1f} сек и пробую снова..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    bot_2(f"Ошибка перевода: {e}\ntext: {text}")
                    return text

        logging.error("[Translator] Все попытки перевода исчерпаны")
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
