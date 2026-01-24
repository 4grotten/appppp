# Архитектура интеграции Faster-Whisper

> Документ описывает текущее состояние системы и целевую архитектуру для интеграции STT (Speech-to-Text) на базе faster-whisper.

## 1. Текущее состояние (AS-IS)

### 1.1 Telegram Bot

**Файлы:**
- `messenger_bots/services/telegram.py` - основной сервис
- `messenger_bots/views.py` - webhook endpoint (line 110)

**Webhook Handler:**
```
Endpoint: /api/v1/messenger-bots/telegram/webhook/{organization_id}/
Class: TelegramWebhookView
Method: process_webhook_update() (line 443)
```

**Текущий Flow обработки сообщений:**
```
┌─────────────────────────────────────────────────────────┐
│              TELEGRAM WEBHOOK                           │
│         /telegram/webhook/{org_id}/                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
        TelegramBotService.process_webhook_update()
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
     /start command         Text Message
           │                     │
      Welcome msg          _handle_message()
      + Return                   │
                                 ▼
                    Save BotMessage (incoming)
                                 │
                                 ▼
                    BotAssistantService.get_response()
                                 │
                                 ▼
                    Parse & Send Response
```

**Методы скачивания файлов (уже есть):**
```python
# telegram.py lines 218-267
_make_request("getFile", {"file_id": file_id})
_download_and_save_photo()  # Паттерн для скачивания
```

**Текущие ограничения:**
- Обрабатываются только текстовые сообщения (line 463)
- Voice/Audio сообщения игнорируются
- Нет конвертации аудио форматов

---

### 1.2 WhatsApp Bot (WAHA)

**Файлы:**
- `messenger_bots/services/whatsapp/waha.py` - WAHA сервис
- `messenger_bots/services/whatsapp/base.py` - базовый интерфейс
- `messenger_bots/views.py` - webhook (line 219)
- `messenger_bots/tasks.py` - async processing (line 488)

**Webhook Handler:**
```
Endpoint: /api/v1/messenger-bots/whatsapp/waha/webhook/
Class: WAHAWebhookView
Method: _handle_message() (line 384)
```

**Текущий Flow:**
```
┌──────────────────────────────────────────────────────────┐
│             WHATSAPP WAHA WEBHOOK                        │
│          /whatsapp/waha/webhook/                         │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
            WAHAWebhookView.post()
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
       message   session.status  message.ack
           │
           ▼
    _handle_message()
           │
           ▼
    Extract: phone, text, pushName
           │
           ▼
    Get/Create BotChat
    Save BotMessage (incoming)
           │
           ▼
    process_whatsapp_message_task.delay()  ← Celery async
           │
           ▼
    [Celery Worker]
    ├─ mark_as_read()
    ├─ send_typing()
    ├─ BotAssistantService.get_response()
    ├─ Parse products
    └─ Send response via WAHA
```

**WAHA Message Structure:**
```python
WhatsAppIncomingMessage(
    message_type="message",
    from_number=phone_number,
    text=payload.get("body", ""),
    has_media=payload.get("hasMedia", False),  # ← Голосовые здесь
    message_id=payload.get("id", ""),
    timestamp=payload.get("timestamp"),
)
```

**Текущие ограничения:**
- `has_media=True` детектируется, но не обрабатывается
- Нет скачивания media из WAHA
- PTT (push-to-talk) сообщения игнорируются

---

### 1.3 AI Assistant

**Файл:** `messenger_bots/services/assistant.py`

**Главная точка входа:**
```python
BotAssistantService.get_response(
    organization: Organization,
    question: str,           # ← Сюда пойдёт транскрипция
    chat_history: List[Dict],
    user_language: str = "ru"
)
```

**Flow AI запроса:**
```
┌──────────────────────────────────────────────────────────┐
│          BotAssistantService.get_response()              │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
            Check response cache
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
      Cache HIT             Cache MISS
      Return cached              │
                                 ▼
                    Load training data:
                    ├─ Q&A pairs (Answer model)
                    ├─ Catalog JSON (if is_catalog=True)
                    ├─ Organization info
                    └─ Marketing info (discounts, coupons)
                                 │
                                 ▼
                    Build system prompt
                    (ai_utils.build_system_prompt)
                                 │
                                 ▼
                    Call OpenAI API
                    (model: gpt-4o-mini)
                                 │
                                 ▼
                    Parse response:
                    ├─ Product detection
                    ├─ ###NEXT### separators
                    └─ Format for platform
```

**Внешний AI endpoint:**
- Provider: OpenAI API
- Model: `gpt-4o-mini`
- Config: `OPENAI_API_KEY` в settings

---

### 1.4 Инфраструктура

**Celery Tasks** (`messenger_bots/tasks.py`):

| Task | Назначение |
|------|------------|
| `process_whatsapp_message_task` | Async обработка WA сообщений |
| `send_telegram_products_task` | Отправка товаров с пагинацией |
| `cache_assistant_training_data` | Кэширование training data (каждые 20 мин) |
| `create_telegram_bot_task` | Создание TG бота через BotFather |

**Кэширование:**
- Django cache для training data
- Key format: `assistant_training_data:{org_id}`
- TTL: 20 минут (periodic task)

---

## 2. Целевое состояние (TO-BE)

### 2.1 Архитектура STT

**Рекомендуемый вариант: Встроенный сервис**

Обоснование:
- Простота интеграции (нет дополнительных сервисов)
- Низкая latency (нет сетевых вызовов)
- faster-whisper base модель требует ~150MB RAM
- Celery workers уже есть для async обработки

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE MESSAGE FLOW                           │
└─────────────────────────────────────────────────────────────────┘

     ┌─────────────┐           ┌─────────────┐
     │  Telegram   │           │  WhatsApp   │
     │   Voice     │           │    PTT      │
     └──────┬──────┘           └──────┬──────┘
            │                         │
            ▼                         ▼
     ┌─────────────┐           ┌─────────────┐
     │  Download   │           │  Download   │
     │  via TG API │           │  via WAHA   │
     └──────┬──────┘           └──────┬──────┘
            │                         │
            └───────────┬─────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   TranscriptionService │
            │   (faster-whisper)     │
            │                        │
            │   ┌─────────────────┐  │
            │   │ Audio Convert   │  │
            │   │ (OGG→WAV/MP3)   │  │
            │   └────────┬────────┘  │
            │            │           │
            │   ┌────────▼────────┐  │
            │   │ Whisper Model   │  │
            │   │ (base, int8)    │  │
            │   └────────┬────────┘  │
            └────────────┼──────────┘
                         │
                         ▼
                  Transcribed Text
                         │
                         ▼
            ┌───────────────────────┐
            │  BotAssistantService  │
            │  .get_response()      │
            │  (без изменений)      │
            └───────────────────────┘
```

### 2.2 Диаграмма компонентов

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND SERVICE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────────────┐ │
│  │   Telegram     │    │    WhatsApp    │    │   NEW: Transcription   │ │
│  │   Service      │    │    Service     │    │   Service              │ │
│  │                │    │    (WAHA)      │    │                        │ │
│  │ ┌────────────┐ │    │ ┌────────────┐ │    │ ┌────────────────────┐ │ │
│  │ │ Text Msg   │ │    │ │ Text Msg   │ │    │ │ transcribe_audio() │ │ │
│  │ │ Handler    │ │    │ │ Handler    │ │    │ │                    │ │ │
│  │ └────────────┘ │    │ └────────────┘ │    │ │ - Load model       │ │ │
│  │ ┌────────────┐ │    │ ┌────────────┐ │    │ │ - Convert format   │ │ │
│  │ │ Voice Msg  │─┼────┼─│ PTT Msg    │─┼────┼─│ - Run inference    │ │ │
│  │ │ Handler    │ │    │ │ Handler    │ │    │ │ - Return text      │ │ │
│  │ └────────────┘ │    │ └────────────┘ │    │ └────────────────────┘ │ │
│  └───────┬────────┘    └───────┬────────┘    └────────────────────────┘ │
│          │                     │                                         │
│          └──────────┬──────────┘                                         │
│                     │                                                    │
│                     ▼                                                    │
│          ┌─────────────────────┐                                         │
│          │  BotAssistantService │                                        │
│          │  (без изменений)     │                                        │
│          └──────────┬──────────┘                                         │
│                     │                                                    │
│                     ▼                                                    │
│          ┌─────────────────────┐                                         │
│          │    OpenAI API       │                                         │
│          │    (gpt-4o-mini)    │                                         │
│          └─────────────────────┘                                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Sequence диаграмма (Telegram Voice)

```
User          Telegram       TelegramService    TranscriptionService    AIService
 │                │                 │                    │                  │
 │──Voice Msg────▶│                 │                    │                  │
 │                │──Webhook───────▶│                    │                  │
 │                │                 │                    │                  │
 │                │                 │──getFile()────────▶│                  │
 │                │                 │◀──file_path────────│                  │
 │                │                 │                    │                  │
 │                │                 │──Download Audio───▶│                  │
 │                │                 │◀──audio_bytes──────│                  │
 │                │                 │                    │                  │
 │                │                 │──transcribe()─────▶│                  │
 │                │                 │                    │──Load Model      │
 │                │                 │                    │──Convert OGG     │
 │                │                 │                    │──Run Whisper     │
 │                │                 │◀──text─────────────│                  │
 │                │                 │                    │                  │
 │                │                 │──get_response(text)───────────────────▶│
 │                │                 │◀──ai_response──────────────────────────│
 │                │                 │                    │                  │
 │                │◀──sendMessage───│                    │                  │
 │◀───Response────│                 │                    │                  │
```

### 2.4 Sequence диаграмма (WhatsApp Voice)

```
User         WAHA        WAHAWebhook      TranscriptionService    CeleryTask    AIService
 │             │              │                    │                  │            │
 │──PTT Msg───▶│              │                    │                  │            │
 │             │──Webhook────▶│                    │                  │            │
 │             │              │                    │                  │            │
 │             │              │──Check hasMedia    │                  │            │
 │             │              │                    │                  │            │
 │             │              │──Download from WAHA│                  │            │
 │             │◀─────────────│──/api/files/...   │                  │            │
 │             │──audio_data─▶│                    │                  │            │
 │             │              │                    │                  │            │
 │             │              │──transcribe()─────▶│                  │            │
 │             │              │◀──text─────────────│                  │            │
 │             │              │                    │                  │            │
 │             │              │──delay(task, text)─────────────────────▶│          │
 │             │              │                    │                  │            │
 │             │              │                    │            [Async Processing]  │
 │             │              │                    │                  │──get_response()─▶│
 │             │              │                    │                  │◀──response──────│
 │             │              │                    │                  │            │
 │             │◀─────────────────────────────────────────────────────│──send_message
 │◀───Response─│              │                    │                  │            │
```

---

## 3. Новые компоненты

### 3.1 TranscriptionService

**Файл:** `messenger_bots/services/transcription.py`

```python
class TranscriptionService:
    """Сервис транскрипции голосовых сообщений через faster-whisper."""

    _model = None  # Singleton для модели

    @classmethod
    def get_model(cls):
        """Lazy loading модели Whisper."""
        if cls._model is None:
            from faster_whisper import WhisperModel
            cls._model = WhisperModel(
                model_size="base",
                device="cpu",
                compute_type="int8"
            )
        return cls._model

    @classmethod
    def transcribe(cls, audio_path: str, language: str = None) -> dict:
        """
        Транскрибировать аудио файл.

        Args:
            audio_path: Путь к аудио файлу
            language: Язык (None для автодетекта)

        Returns:
            {
                "text": "транскрибированный текст",
                "language": "ru",
                "duration": 15.5,
                "confidence": 0.95
            }
        """
        model = cls.get_model()
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5
        )

        text = " ".join([seg.text for seg in segments])

        return {
            "text": text.strip(),
            "language": info.language,
            "duration": info.duration,
            "confidence": info.language_probability
        }
```

### 3.2 Модификация TelegramService

**Файл:** `messenger_bots/services/telegram.py`

```python
# В _handle_message() добавить:

def _handle_voice_message(self, message: dict, chat: BotChat) -> str:
    """Обработка голосового сообщения."""
    voice = message.get("voice") or message.get("audio")
    if not voice:
        return None

    file_id = voice.get("file_id")

    # 1. Получить путь к файлу
    file_info = self._make_request("getFile", {"file_id": file_id})
    file_path = file_info.get("result", {}).get("file_path")

    # 2. Скачать файл
    download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
    audio_content = requests.get(download_url).content

    # 3. Сохранить временно
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(audio_content)
        temp_path = f.name

    # 4. Транскрибировать
    try:
        result = TranscriptionService.transcribe(temp_path)
        return result["text"]
    finally:
        os.unlink(temp_path)
```

### 3.3 Модификация WAHA Handler

**Файл:** `messenger_bots/views.py`

```python
# В _handle_message() добавить:

def _download_waha_media(self, whatsapp_bot, message_id: str) -> bytes:
    """Скачать медиа файл из WAHA."""
    service = WhatsAppServiceFactory.get_service(whatsapp_bot)
    url = f"{service.base_url}/api/{service.session_name}/messages/{message_id}/download"
    response = requests.get(url, headers=service._get_headers())
    return response.content

# В _handle_message():
if payload.get("hasMedia"):
    message_id = payload.get("id", {}).get("id", "")
    media_type = payload.get("type", "")

    if media_type in ("ptt", "audio"):  # ptt = push-to-talk
        audio_content = self._download_waha_media(whatsapp_bot, message_id)
        # Транскрибировать и использовать как message_body
```

---

## 4. Зависимости и риски

### 4.1 Новые зависимости

```txt
# requirements.txt
faster-whisper>=0.10.0
# Опционально для конвертации:
pydub>=0.25.0  # Если нужна конвертация форматов
ffmpeg-python>=0.2.0  # Альтернатива pydub
```

### 4.2 Системные требования

| Компонент | Минимум | Рекомендуемо |
|-----------|---------|--------------|
| RAM (модель base) | 300MB | 512MB |
| CPU | 2 cores | 4 cores |
| Disk (модель) | 150MB | 150MB |
| Disk (temp files) | 50MB | 100MB |

### 4.3 Риски и митигации

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| OOM при загрузке модели | Низкая | Высокое | int8 quantization, мониторинг памяти |
| Долгая обработка (>30 сек аудио) | Средняя | Среднее | Лимит 5 мин, показывать typing |
| Качество распознавания шума | Средняя | Среднее | Проверять confidence, fallback |
| WAHA media download fails | Низкая | Высокое | Retry механизм, error handling |
| Формат аудио не поддерживается | Низкая | Среднее | Конвертация через ffmpeg |

### 4.4 Ограничения

- Максимальная длина аудио: **5 минут**
- Поддерживаемые форматы: OGG, OPUS, MP3, WAV, M4A, FLAC
- Языки: автодетект (ru, en приоритет)
- Модель: faster-whisper base (баланс скорость/качество)
