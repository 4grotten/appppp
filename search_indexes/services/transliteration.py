from transliterate import translit, detect_language


class Transliteration:

    def _get_ru_text(text: str):
        return translit(text, language_code='ru')

    def _get_en_text(text: str):
        return translit(text, reversed=True)

    @classmethod
    def get_translit(cls, text: str):
        return cls._get_en_text(text) if detect_language(text) == 'ru' else cls._get_ru_text(text)
