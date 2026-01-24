# Техническое задание: Интеграция STT (Faster-Whisper)

## 1. Общие сведения

| Параметр | Значение |
|----------|----------|
| Название | Speech-to-Text модуль для AI-ассистента |
| Версия документа | 1.0 |
| Дата | 2026-01-22 |
| Статус | Draft |

### 1.1 Глоссарий

| Термин | Определение |
|--------|-------------|
| STT | Speech-to-Text — преобразование речи в текст |
| PTT | Push-to-Talk — голосовое сообщение (WhatsApp) |
| WAHA | WhatsApp HTTP API — self-hosted сервис для WhatsApp |
| faster-whisper | Оптимизированная версия OpenAI Whisper |

---

## 2. Цели и задачи

### 2.1 Бизнес-цели

| # | Цель | Метрика успеха |
|---|------|----------------|
| B1 | Расширить каналы взаимодействия с AI-ассистентом | Пользователи могут отправлять голосовые |
| B2 | Улучшить UX для мобильных пользователей | Голосовые обрабатываются как текст |
| B3 | Конкурентное преимущество | Функционал доступен без доплаты |

### 2.2 Технические цели

| # | Цель | Метрика успеха |
|---|------|----------------|
| T1 | Интеграция STT в Telegram бота | Voice → Text → AI → Response |
| T2 | Интеграция STT в WhatsApp бота | PTT → Text → AI → Response |
| T3 | Минимальное влияние на latency | < 5 сек для 30 сек аудио |
| T4 | Надёжность распознавания | > 90% для чистой речи |

---

## 3. Функциональные требования

### FR-001: Обработка голосовых сообщений Telegram

| ID | Требование | Приоритет | Статус |
|----|------------|-----------|--------|
| FR-001.1 | Система должна детектировать voice и audio сообщения в Telegram | Must | ⬜ |
| FR-001.2 | Система должна скачивать аудио файл через Telegram Bot API | Must | ⬜ |
| FR-001.3 | Система должна конвертировать OGG/OPUS в поддерживаемый формат | Should | ⬜ |
| FR-001.4 | Система должна транскрибировать аудио через faster-whisper | Must | ⬜ |
| FR-001.5 | Система должна передавать транскрипцию в AI-ассистент | Must | ⬜ |
| FR-001.6 | Система должна показывать typing indicator во время обработки | Should | ⬜ |
| FR-001.7 | Система должна сохранять транскрипцию в BotMessage | Must | ⬜ |

**Acceptance Criteria FR-001:**
```gherkin
Given пользователь отправляет голосовое сообщение в Telegram бота
When сообщение обработано
Then пользователь получает текстовый ответ от AI-ассистента
And транскрипция сохранена в истории чата
```

---

### FR-002: Обработка голосовых сообщений WhatsApp

| ID | Требование | Приоритет | Статус |
|----|------------|-----------|--------|
| FR-002.1 | Система должна детектировать PTT и audio сообщения в WAHA webhook | Must | ⬜ |
| FR-002.2 | Система должна скачивать media файл через WAHA API | Must | ⬜ |
| FR-002.3 | Система должна обрабатывать форматы: OGG, OPUS, MP3, M4A | Must | ⬜ |
| FR-002.4 | Система должна транскрибировать аудио через faster-whisper | Must | ⬜ |
| FR-002.5 | Система должна передавать транскрипцию в AI-ассистент | Must | ⬜ |
| FR-002.6 | Система должна показывать typing indicator (WAHA API) | Should | ⬜ |
| FR-002.7 | Система должна сохранять транскрипцию в BotMessage | Must | ⬜ |

**Acceptance Criteria FR-002:**
```gherkin
Given пользователь отправляет голосовое сообщение в WhatsApp
When WAHA доставляет webhook
Then система скачивает и транскрибирует аудио
And пользователь получает текстовый ответ от AI
```

---

### FR-003: TranscriptionService

| ID | Требование | Приоритет | Статус |
|----|------------|-----------|--------|
| FR-003.1 | Сервис должен использовать faster-whisper модель "base" | Must | ⬜ |
| FR-003.2 | Модель должна загружаться lazy (при первом вызове) | Must | ⬜ |
| FR-003.3 | Сервис должен автоматически определять язык аудио | Must | ⬜ |
| FR-003.4 | Сервис должен возвращать: text, language, duration, confidence | Must | ⬜ |
| FR-003.5 | Сервис должен обрабатывать ошибки и возвращать понятные сообщения | Must | ⬜ |
| FR-003.6 | Сервис должен логировать время транскрипции | Should | ⬜ |
| FR-003.7 | Сервис должен поддерживать принудительное указание языка | Could | ⬜ |

**API контракт:**
```python
class TranscriptionService:
    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Транскрибировать аудио файл.

        Args:
            audio_path: Путь к аудио файлу (локальный)
            language: Код языка (ru, en) или None для автодетекта

        Returns:
            TranscriptionResult:
                text: str - транскрибированный текст
                language: str - определённый язык
                duration: float - длительность аудио (сек)
                confidence: float - уверенность в языке (0-1)

        Raises:
            TranscriptionError: При ошибке транскрипции
            AudioTooLongError: Если аудио > MAX_DURATION
            UnsupportedFormatError: Если формат не поддерживается
        """
```

---

### FR-004: Обработка ошибок

| ID | Требование | Приоритет | Статус |
|----|------------|-----------|--------|
| FR-004.1 | При ошибке скачивания файла — уведомить пользователя | Must | ⬜ |
| FR-004.2 | При ошибке транскрипции — уведомить пользователя | Must | ⬜ |
| FR-004.3 | При превышении лимита длительности — уведомить пользователя | Must | ⬜ |
| FR-004.4 | Все ошибки должны логироваться с context | Must | ⬜ |
| FR-004.5 | Retry для transient network errors (скачивание) | Should | ⬜ |

**Сообщения пользователю:**
```yaml
voice_processing_error:
  ru: "Не удалось обработать голосовое сообщение. Попробуйте ещё раз или напишите текстом."
  en: "Failed to process voice message. Please try again or send a text message."

voice_too_long:
  ru: "Голосовое сообщение слишком длинное (максимум 5 минут). Пожалуйста, запишите короче."
  en: "Voice message is too long (max 5 minutes). Please record a shorter one."

voice_download_error:
  ru: "Не удалось загрузить голосовое сообщение. Попробуйте ещё раз."
  en: "Failed to download voice message. Please try again."
```

---

## 4. Нефункциональные требования

### NFR-001: Производительность

| ID | Метрика | Целевое значение | Критичность |
|----|---------|------------------|-------------|
| NFR-001.1 | Время транскрипции (аудио до 30 сек) | < 3 сек | High |
| NFR-001.2 | Время транскрипции (аудио 30-60 сек) | < 6 сек | Medium |
| NFR-001.3 | Время транскрипции (аудио 1-5 мин) | < 30 сек | Low |
| NFR-001.4 | Время загрузки модели | < 5 сек | Medium |
| NFR-001.5 | Общий response time (voice → AI answer) | < 10 сек (для 30 сек аудио) | High |

### NFR-002: Надёжность

| ID | Метрика | Целевое значение | Критичность |
|----|---------|------------------|-------------|
| NFR-002.1 | Uptime STT сервиса | 99.5% | High |
| NFR-002.2 | Качество распознавания (чистая речь) | > 95% | High |
| NFR-002.3 | Качество распознавания (шумная речь) | > 80% | Medium |
| NFR-002.4 | Обработка ошибок без crash | 100% | High |

### NFR-003: Масштабируемость

| ID | Метрика | Целевое значение | Критичность |
|----|---------|------------------|-------------|
| NFR-003.1 | Параллельная обработка | 5+ одновременно | Medium |
| NFR-003.2 | Memory usage (модель loaded) | < 500MB | High |
| NFR-003.3 | Memory usage (при транскрипции) | < 1GB peak | High |

### NFR-004: Безопасность

| ID | Требование | Критичность |
|----|------------|-------------|
| NFR-004.1 | Аудио файлы удаляются после обработки | High |
| NFR-004.2 | Временные файлы хранятся в защищённой директории | High |
| NFR-004.3 | Нет логирования содержимого аудио/транскрипции | High |

---

## 5. Ограничения

### 5.1 Технические ограничения

| Ограничение | Значение | Обоснование |
|-------------|----------|-------------|
| Модель Whisper | base | Баланс качество/скорость/память |
| Max длительность аудио | 5 минут | Предотвращение DoS, память |
| Поддерживаемые языки | ru, en (auto) | Основная аудитория |
| Device | CPU | Нет GPU на серверах |
| Compute type | int8 | Экономия памяти |

### 5.2 Бизнес-ограничения

| Ограничение | Значение |
|-------------|----------|
| Бюджет на инфраструктуру | $0 (self-hosted) |
| Внешние API | Не использовать |
| Timeline | 1 неделя |

---

## 6. Архитектура и интеграция

### 6.1 Компонентная диаграмма

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────────────────┐  │
│  │ TelegramService  │         │ TranscriptionService         │  │
│  │                  │         │                              │  │
│  │ ┌──────────────┐ │         │  ┌────────────────────────┐  │  │
│  │ │ Voice Handler│─┼─────────┼─▶│ transcribe(audio_path) │  │  │
│  │ └──────────────┘ │         │  └────────────────────────┘  │  │
│  │ ┌──────────────┐ │         │              │               │  │
│  │ │ Download File│ │         │              ▼               │  │
│  │ └──────────────┘ │         │  ┌────────────────────────┐  │  │
│  └──────────────────┘         │  │ faster-whisper model   │  │  │
│                               │  │ (base, int8, CPU)      │  │  │
│  ┌──────────────────┐         │  └────────────────────────┘  │  │
│  │ WAHAService      │         │              │               │  │
│  │                  │         │              ▼               │  │
│  │ ┌──────────────┐ │         │  ┌────────────────────────┐  │  │
│  │ │ PTT Handler  │─┼─────────┼─▶│ TranscriptionResult    │  │  │
│  │ └──────────────┘ │         │  │ {text, lang, duration} │  │  │
│  │ ┌──────────────┐ │         │  └────────────────────────┘  │  │
│  │ │ Download Media│ │         │                              │  │
│  │ └──────────────┘ │         └──────────────────────────────┘  │
│  └──────────────────┘                       │                    │
│           │                                 │                    │
│           └─────────────┬───────────────────┘                    │
│                         │                                        │
│                         ▼                                        │
│              ┌─────────────────────┐                             │
│              │ BotAssistantService │                             │
│              │ .get_response(text) │                             │
│              └─────────────────────┘                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Sequence Diagram

```
┌──────┐      ┌────────────┐      ┌─────────────────┐      ┌───────────┐      ┌────────┐
│ User │      │ Telegram   │      │ TelegramService │      │ STTService│      │   AI   │
└──┬───┘      └─────┬──────┘      └────────┬────────┘      └─────┬─────┘      └───┬────┘
   │                │                      │                     │                │
   │ Voice Message  │                      │                     │                │
   │───────────────▶│                      │                     │                │
   │                │                      │                     │                │
   │                │    Webhook           │                     │                │
   │                │─────────────────────▶│                     │                │
   │                │                      │                     │                │
   │                │                      │ getFile()           │                │
   │                │                      │────────────────────▶│                │
   │                │                      │◀────────────────────│                │
   │                │                      │ file_path           │                │
   │                │                      │                     │                │
   │                │                      │ download()          │                │
   │                │◀─────────────────────│                     │                │
   │                │ audio bytes          │                     │                │
   │                │─────────────────────▶│                     │                │
   │                │                      │                     │                │
   │                │                      │ transcribe()        │                │
   │                │                      │────────────────────▶│                │
   │                │                      │                     │ load model     │
   │                │                      │                     │ (if not loaded)│
   │                │                      │                     │                │
   │                │                      │                     │ run inference  │
   │                │                      │◀────────────────────│                │
   │                │                      │ {text, lang, ...}   │                │
   │                │                      │                     │                │
   │                │                      │ get_response(text)  │                │
   │                │                      │────────────────────────────────────▶│
   │                │                      │◀────────────────────────────────────│
   │                │                      │ ai_response         │                │
   │                │                      │                     │                │
   │                │  sendMessage         │                     │                │
   │                │◀─────────────────────│                     │                │
   │◀───────────────│                      │                     │                │
   │  AI Response   │                      │                     │                │
   │                │                      │                     │                │
```

---

## 7. API контракты

### 7.1 TranscriptionService Internal API

```python
# messenger_bots/services/transcription.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class TranscriptionResult:
    """Результат транскрипции."""
    text: str                    # Транскрибированный текст
    language: str                # Определённый язык (ru, en, ...)
    duration: float              # Длительность аудио в секундах
    confidence: float            # Уверенность в языке (0.0 - 1.0)


class TranscriptionError(Exception):
    """Базовая ошибка транскрипции."""
    pass


class AudioTooLongError(TranscriptionError):
    """Аудио превышает максимальную длительность."""
    pass


class UnsupportedFormatError(TranscriptionError):
    """Формат аудио не поддерживается."""
    pass


class TranscriptionService:
    """Сервис транскрипции голосовых сообщений."""

    SUPPORTED_FORMATS = {'.ogg', '.oga', '.opus', '.mp3', '.wav', '.m4a', '.flac'}
    MAX_DURATION_SECONDS = 300  # 5 минут

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Транскрибировать аудио файл.

        Args:
            audio_path: Абсолютный путь к аудио файлу
            language: Код языка для форсирования (None = автодетект)

        Returns:
            TranscriptionResult с текстом и метаданными

        Raises:
            TranscriptionError: Общая ошибка транскрипции
            AudioTooLongError: Аудио длиннее MAX_DURATION_SECONDS
            UnsupportedFormatError: Неподдерживаемый формат файла
            FileNotFoundError: Файл не найден
        """
        pass

    @classmethod
    def is_supported_format(cls, file_path: str) -> bool:
        """Проверить, поддерживается ли формат файла."""
        pass

    @classmethod
    def get_audio_duration(cls, file_path: str) -> float:
        """Получить длительность аудио в секундах."""
        pass
```

### 7.2 Telegram Voice Handler

```python
# В messenger_bots/services/telegram.py

class TelegramBotService:

    def _handle_voice_message(
        self,
        message: dict,
        chat: BotChat,
        user_language: str
    ) -> Optional[str]:
        """
        Обработать голосовое сообщение.

        Args:
            message: Telegram message object с voice/audio
            chat: BotChat объект
            user_language: Язык пользователя

        Returns:
            Транскрибированный текст или None при ошибке
        """
        pass

    def _download_telegram_file(self, file_id: str) -> bytes:
        """
        Скачать файл из Telegram.

        Args:
            file_id: Telegram file_id

        Returns:
            Содержимое файла в bytes

        Raises:
            TelegramAPIError: Ошибка Telegram API
        """
        pass
```

### 7.3 WAHA Media Handler

```python
# В messenger_bots/services/whatsapp/waha.py

class WAHAService:

    def download_media(self, message_id: str) -> bytes:
        """
        Скачать медиа файл из WAHA.

        Args:
            message_id: ID сообщения с медиа

        Returns:
            Содержимое файла в bytes

        Raises:
            WAHAAPIError: Ошибка WAHA API
        """
        pass
```

---

## 8. Чеклист готовности

### 8.1 Разработка

| # | Задача | Ответственный | Статус |
|---|--------|---------------|--------|
| D1 | TranscriptionService создан | | ⬜ |
| D2 | Whisper модель загружается корректно | | ⬜ |
| D3 | Транскрипция работает для OGG | | ⬜ |
| D4 | Транскрипция работает для MP3 | | ⬜ |
| D5 | Error handling реализован | | ⬜ |
| D6 | Logging добавлен | | ⬜ |
| D7 | Временные файлы cleanup | | ⬜ |

### 8.2 Telegram интеграция

| # | Задача | Ответственный | Статус |
|---|--------|---------------|--------|
| T1 | Voice message detection | | ⬜ |
| T2 | File download через Bot API | | ⬜ |
| T3 | STT service integration | | ⬜ |
| T4 | Typing indicator | | ⬜ |
| T5 | Error messages для пользователя | | ⬜ |
| T6 | BotMessage сохраняется с транскрипцией | | ⬜ |

### 8.3 WhatsApp интеграция

| # | Задача | Ответственный | Статус |
|---|--------|---------------|--------|
| W1 | PTT message detection (hasMedia) | | ⬜ |
| W2 | Media download через WAHA | | ⬜ |
| W3 | STT service integration | | ⬜ |
| W4 | Typing indicator (WAHA) | | ⬜ |
| W5 | Error messages для пользователя | | ⬜ |
| W6 | BotMessage сохраняется с транскрипцией | | ⬜ |

### 8.4 Тестирование

| # | Задача | Ответственный | Статус |
|---|--------|---------------|--------|
| Q1 | Unit tests: TranscriptionService | | ⬜ |
| Q2 | Unit tests: Telegram voice handler | | ⬜ |
| Q3 | Unit tests: WAHA media handler | | ⬜ |
| Q4 | Integration test: TG voice → AI | | ⬜ |
| Q5 | Integration test: WA PTT → AI | | ⬜ |
| Q6 | Load test: 10 concurrent requests | | ⬜ |
| Q7 | Manual QA: разные языки | | ⬜ |
| Q8 | Manual QA: шумные записи | | ⬜ |

### 8.5 DevOps

| # | Задача | Ответственный | Статус |
|---|--------|---------------|--------|
| O1 | Dockerfile обновлен (ffmpeg) | | ⬜ |
| O2 | requirements.txt обновлен | | ⬜ |
| O3 | Memory limits настроены | | ⬜ |
| O4 | Health checks добавлены | | ⬜ |
| O5 | Prometheus metrics | | ⬜ |
| O6 | Alerting rules | | ⬜ |

### 8.6 Документация

| # | Задача | Ответственный | Статус |
|---|--------|---------------|--------|
| DOC1 | README обновлен | | ⬜ |
| DOC2 | Inline comments | | ⬜ |
| DOC3 | Deployment guide | | ⬜ |

---

## 9. Риски и митигации

| # | Риск | Вероятность | Влияние | Митигация | Статус |
|---|------|-------------|---------|-----------|--------|
| R1 | OOM при загрузке модели | Низкая | Высокое | int8 quantization, мониторинг памяти | ⬜ |
| R2 | Долгая обработка (>30 сек аудио) | Высокая | Среднее | Лимит 5 мин, typing indicator | ⬜ |
| R3 | Низкое качество распознавания шума | Средняя | Среднее | Проверять confidence, fallback message | ⬜ |
| R4 | WAHA media download fails | Низкая | Высокое | Retry механизм, graceful degradation | ⬜ |
| R5 | Неподдерживаемый формат аудио | Низкая | Среднее | Конвертация через ffmpeg | ⬜ |
| R6 | Telegram file_id expired | Средняя | Среднее | Немедленная обработка при получении | ⬜ |
| R7 | Concurrent requests overload | Средняя | Среднее | Очередь задач, rate limiting | ⬜ |

---

## 10. Timeline

| Этап | Длительность | Начало | Окончание | Статус |
|------|--------------|--------|-----------|--------|
| Подготовка инфраструктуры | 0.5 дня | День 1 | День 1 | ⬜ |
| TranscriptionService | 1 день | День 1 | День 2 | ⬜ |
| Telegram интеграция | 1 день | День 2 | День 3 | ⬜ |
| WhatsApp интеграция | 1 день | День 3 | День 4 | ⬜ |
| UX улучшения | 0.5 дня | День 4 | День 4 | ⬜ |
| Тестирование | 1 день | День 5 | День 5 | ⬜ |
| DevOps и деплой | 0.5 дня | День 6 | День 6 | ⬜ |
| **ИТОГО** | **5.5 дней** | | | |

---

## 11. Acceptance Criteria (Summary)

### Telegram Voice
```gherkin
Feature: Telegram Voice Message Processing

  Scenario: Successful voice transcription
    Given пользователь в активном чате с AI-ассистентом
    When пользователь отправляет голосовое сообщение длительностью 15 секунд
    Then система показывает typing indicator
    And система транскрибирует аудио за < 3 секунды
    And пользователь получает ответ от AI на основе транскрипции
    And транскрипция сохранена в истории чата

  Scenario: Voice message too long
    Given пользователь в активном чате
    When пользователь отправляет голосовое сообщение длительностью 7 минут
    Then пользователь получает сообщение об ограничении (max 5 минут)
```

### WhatsApp Voice
```gherkin
Feature: WhatsApp PTT Message Processing

  Scenario: Successful PTT transcription
    Given пользователь в активном WhatsApp чате
    When пользователь отправляет PTT сообщение
    Then система скачивает аудио из WAHA
    And система транскрибирует аудио
    And пользователь получает ответ от AI
```

---

## 12. Sign-off

| Роль | Имя | Дата | Подпись |
|------|-----|------|---------|
| Product Owner | | | |
| Tech Lead | | | |
| Backend Developer | | | |
| QA Engineer | | | |
| DevOps | | | |

---

*Документ создан: 2026-01-22*
*Последнее обновление: 2026-01-22*
