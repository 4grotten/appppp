# План интеграции Faster-Whisper

> Пошаговый план работ по добавлению распознавания голосовых сообщений в AI-ассистент.

## Обзор

| Параметр | Значение |
|----------|----------|
| Общая длительность | 5-6 рабочих дней |
| Сложность | Средняя |
| Риск | Низкий |
| Зависимости | faster-whisper, ffmpeg (опционально) |

---

## Этап 1: Подготовка инфраструктуры (0.5 дня)

### 1.1 Установка зависимостей
- [ ] Добавить `faster-whisper>=0.10.0` в requirements.txt
- [ ] Добавить `pydub>=0.25.0` для конвертации аудио (опционально)
- [ ] Проверить наличие ffmpeg в Docker образе
- [ ] Обновить Dockerfile если нужно

```dockerfile
# Добавить в Dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

### 1.2 Конфигурация
- [ ] Добавить настройки в `settings/base.py`:
  ```python
  # Faster-Whisper STT
  WHISPER_MODEL_SIZE = env("WHISPER_MODEL_SIZE", default="base")
  WHISPER_DEVICE = env("WHISPER_DEVICE", default="cpu")
  WHISPER_COMPUTE_TYPE = env("WHISPER_COMPUTE_TYPE", default="int8")
  WHISPER_MAX_AUDIO_DURATION = 300  # секунд
  ```

### 1.3 Тестирование базовой установки
- [ ] Проверить импорт faster-whisper в Django shell
- [ ] Загрузить модель, замерить время и память
- [ ] Проверить транскрипцию тестового файла

---

## Этап 2: Разработка TranscriptionService (1 день)

### 2.1 Создание сервиса
- [ ] Создать файл `messenger_bots/services/transcription.py`
- [ ] Реализовать lazy loading модели (singleton)
- [ ] Реализовать метод `transcribe(audio_path, language)`
- [ ] Добавить обработку ошибок

**Структура файла:**
```python
messenger_bots/services/transcription.py
├── TranscriptionService (class)
│   ├── _model: WhisperModel (class variable)
│   ├── get_model() -> WhisperModel
│   ├── transcribe(audio_path, language) -> dict
│   └── is_supported_format(file_path) -> bool
├── AudioConverter (class, optional)
│   ├── convert_to_wav(input_path) -> str
│   └── get_duration(file_path) -> float
└── TranscriptionError (exception)
```

### 2.2 Конвертация аудио
- [ ] Реализовать конвертацию OGG/OPUS → WAV (если нужно)
- [ ] Добавить проверку длительности аудио
- [ ] Добавить cleanup временных файлов

### 2.3 Unit тесты
- [ ] Тест загрузки модели
- [ ] Тест транскрипции WAV файла
- [ ] Тест транскрипции OGG файла
- [ ] Тест обработки ошибок (битый файл, слишком длинный)

---

## Этап 3: Интеграция с Telegram (1 день)

### 3.1 Детекция голосовых сообщений
- [ ] Модифицировать `telegram.py:process_webhook_update()`
- [ ] Добавить проверку `message.get("voice")` и `message.get("audio")`
- [ ] Роутинг на новый handler

### 3.2 Скачивание аудио
- [ ] Реализовать `_download_voice_file(file_id)` в TelegramBotService
- [ ] Использовать существующий паттерн из `_download_and_save_photo()`
- [ ] Сохранение во временный файл

### 3.3 Обработка и ответ
- [ ] Показать "распознаю голосовое сообщение..." (typing action)
- [ ] Вызвать TranscriptionService.transcribe()
- [ ] Сохранить транскрипцию как текст сообщения
- [ ] Передать в BotAssistantService.get_response()
- [ ] Отправить ответ AI

### 3.4 Integration тесты
- [ ] Тест полного flow: voice → transcription → AI → response
- [ ] Тест fallback при ошибке транскрипции
- [ ] Тест с разными форматами аудио

---

## Этап 4: Интеграция с WhatsApp WAHA (1 день)

### 4.1 Расширение WAHA сервиса
- [ ] Добавить метод `download_media(message_id)` в WAHAService
- [ ] Изучить WAHA API для получения media
- [ ] Обработка PTT (push-to-talk) сообщений

### 4.2 Модификация webhook handler
- [ ] Модифицировать `views.py:WAHAWebhookView._handle_message()`
- [ ] Проверка `hasMedia` и `type` (ptt, audio)
- [ ] Скачивание и транскрипция перед созданием task

### 4.3 Обновление Celery task
- [ ] Обновить `process_whatsapp_message_task()` если нужно
- [ ] Или: транскрипция в webhook handler (синхронно)
- [ ] Fallback при ошибках

### 4.4 Integration тесты
- [ ] Тест PTT сообщения → транскрипция → ответ
- [ ] Тест обычного audio сообщения
- [ ] Тест ошибок (недоступное media, битый файл)

---

## Этап 5: UX улучшения (0.5 дня)

### 5.1 Индикаторы обработки
- [ ] Telegram: "Распознаю голосовое сообщение..."
- [ ] WhatsApp: Typing indicator на время транскрипции
- [ ] Логирование времени обработки

### 5.2 Обработка ошибок
- [ ] Сообщение пользователю при ошибке транскрипции
- [ ] Сообщение при слишком длинном аудио
- [ ] Retry механизм для network errors

### 5.3 Сохранение метаданных
- [ ] Опционально: добавить поля в BotMessage
  - `message_type` (text, voice, audio)
  - `voice_duration` (секунды)
  - `original_file_id` (для Telegram)

---

## Этап 6: Тестирование (1 день)

### 6.1 Unit тесты
- [ ] TranscriptionService: все методы
- [ ] TelegramService: voice handling
- [ ] WAHAService: media download

### 6.2 Integration тесты
- [ ] Telegram: полный flow
- [ ] WhatsApp: полный flow
- [ ] Edge cases: длинные аудио, шумные, разные языки

### 6.3 Load тестирование
- [ ] Параллельная обработка 10 голосовых
- [ ] Memory usage при пиковой нагрузке
- [ ] Время отклика при разной длине аудио

### 6.4 Manual QA
- [ ] Telegram: отправить голосовое → получить ответ AI
- [ ] WhatsApp: отправить PTT → получить ответ AI
- [ ] Проверить разные языки (ru, en)
- [ ] Проверить шумные записи

---

## Этап 7: DevOps и деплой (0.5 дня)

### 7.1 Docker
- [ ] Обновить Dockerfile (ffmpeg, dependencies)
- [ ] Проверить размер образа
- [ ] Настроить memory limits для воркеров

### 7.2 Мониторинг
- [ ] Добавить метрики:
  - `whisper_transcription_duration_seconds`
  - `whisper_transcription_errors_total`
  - `whisper_model_loaded` (gauge)
- [ ] Алерты на высокую latency

### 7.3 Деплой
- [ ] Деплой на staging
- [ ] Smoke тесты
- [ ] Деплой на production
- [ ] Мониторинг первых часов

---

## Чеклист готовности к деплою

### Код
- [ ] TranscriptionService создан и протестирован
- [ ] Telegram voice handling работает
- [ ] WhatsApp PTT handling работает
- [ ] Error handling для всех edge cases
- [ ] Logging добавлен

### Тесты
- [ ] Unit tests проходят
- [ ] Integration tests проходят
- [ ] Manual QA пройдено

### Инфраструктура
- [ ] Dockerfile обновлен
- [ ] docker-compose.yml обновлен (если нужно)
- [ ] Memory limits настроены
- [ ] Мониторинг настроен

### Документация
- [ ] README обновлен
- [ ] Комментарии в коде
- [ ] API документация (если применимо)

---

## Timeline (визуализация)

```
День 1  │ День 2  │ День 3  │ День 4  │ День 5  │ День 6
────────┼─────────┼─────────┼─────────┼─────────┼────────
Подгот. │ Service │ Telegram│ WhatsApp│  Тесты  │ Деплой
  0.5д  │   1д    │   1д    │   1д    │   1д    │  0.5д
────────┴─────────┴─────────┴─────────┴─────────┴────────
        │                   │                   │
        ▼                   ▼                   ▼
   TranscriptionService  Интеграции        Production
      готов              готовы              ready
```

---

## Ресурсы

### Документация
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Telegram Bot API - getFile](https://core.telegram.org/bots/api#getfile)
- [WAHA Docs - Media](https://waha.devlike.pro/docs/how-to/media/)

### Тестовые файлы
- Подготовить 5-10 тестовых аудио разной длины и качества
- Форматы: OGG, MP3, WAV
- Языки: ru, en

### Контакты
- Backend: [имя разработчика]
- DevOps: [имя]
- QA: [имя]
