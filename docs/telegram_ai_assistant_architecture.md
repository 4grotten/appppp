# Архитектура системы Telegram AI-ассистентов

## Обзор

Система позволяет организациям создавать AI-ассистентов для Telegram ботов, которые автоматически отвечают на вопросы клиентов, показывают товары из каталога и обрабатывают запросы.

## Компонентная диаграмма

```mermaid
graph TB
    subgraph "Клиентские приложения"
        WebApp[Web Application]
        MobileApp[Mobile App]
    end

    subgraph "External Services"
        TelegramAPI[Telegram Bot API]
        WAHA[WAHA WhatsApp API]
        OpenAI[OpenAI API Proxy]
        BotFather[BotFather via Telethon]
    end

    subgraph "Backend Django"
        subgraph "API Layer"
            REST[REST API Views]
            Webhooks[Webhook Handlers]
        end

        subgraph "Service Layer"
            TelegramService[TelegramBotService]
            AssistantService[BotAssistantService]
            BotFactoryService[BotFactoryService]
            SubscriptionService[SubscriptionService]
        end

        subgraph "Data Layer"
            Models[(PostgreSQL)]
            Cache[(Redis Cache)]
        end
    end

    subgraph "Async Processing"
        Celery[Celery Workers]
        RabbitMQ[(RabbitMQ)]
    end

    WebApp --> REST
    MobileApp --> REST

    TelegramAPI --> Webhooks
    WAHA --> Webhooks

    REST --> TelegramService
    REST --> AssistantService
    REST --> SubscriptionService

    Webhooks --> TelegramService

    TelegramService --> AssistantService
    TelegramService --> TelegramAPI

    AssistantService --> OpenAI
    AssistantService --> Cache

    BotFactoryService --> BotFather

    TelegramService --> Models
    AssistantService --> Models
    SubscriptionService --> Models

    REST --> Celery
    Celery --> RabbitMQ
```

## Основные компоненты

### 1. API Layer

| Компонент | Файл | Описание |
|-----------|------|----------|
| TelegramBotAPIView | `views.py:528-687` | CRUD для Telegram ботов |
| AutoCreateTelegramBotAPIView | `views.py:1123-1281` | Автосоздание ботов |
| TelegramWebhookView | `views.py:155-335` | Обработка webhook от Telegram |
| OrganizationAssistantView | `assistant_views.py` | Управление AI-ассистентами |

### 2. Service Layer

| Сервис | Файл | Ответственность |
|--------|------|-----------------|
| **TelegramBotService** | `services/telegram.py` | Взаимодействие с Telegram API |
| **BotAssistantService** | `services/assistant.py` | Генерация AI ответов |
| **BotFactoryService** | `services/bot_factory.py` | Создание ботов через BotFather |
| **UserbotAuthService** | `services/bot_factory.py` | Аутентификация Telethon userbot |
| **SubscriptionService** | `subscription_services.py` | Управление подписками |

### 3. Data Layer

#### Модели ботов (`messenger_bots/models.py`)

| Модель | Связи | Назначение |
|--------|-------|------------|
| **TelegramBot** | Organization (1:1) | Конфигурация Telegram бота |
| **WhatsAppBot** | Organization (1:1) | Конфигурация WhatsApp бота |
| **BotChat** | Organization (FK) | Чат с пользователем |
| **BotMessage** | BotChat (FK) | Сообщения в чате |
| **BotCreationRequest** | Organization (FK) | Запрос на создание бота |
| **TelegramUserbot** | - | Userbot для BotFather |

#### Модели подписок (`organizations/models.py`)

| Модель | Связи | Назначение |
|--------|-------|------------|
| **Organization** | User (owner) | Организация |
| **Assistant** | Organization (1:1) | AI-ассистент |
| **UserOrgSubscription** | Organization, User | Платная подписка |
| **RegionalTariff** | Country | Тарифный план |
| **Answer** | Assistant, Question | База знаний |

### 4. Async Processing (Celery)

| Задача | Очередь | Описание |
|--------|---------|----------|
| `create_telegram_bot_task` | messenger_bots | Создание бота через BotFather |
| `send_telegram_products_task` | messenger_bots | Отправка товаров с пагинацией |
| `process_whatsapp_message_task` | messenger_bots | Обработка WhatsApp сообщений |
| `cache_assistant_training_data` | messenger_bots | Кеширование данных AI |
| `check_pending_bot_requests` | messenger_bots | Проверка зависших запросов |

## Потоки данных

### Создание бота (Auto-create Flow)

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Celery
    participant Userbot
    participant BotFather
    participant TelegramAPI

    Client->>API: POST /auto-create/{org_id}/
    API->>DB: Create BotCreationRequest (PENDING)
    API->>Celery: create_telegram_bot_task.delay()
    API-->>Client: 202 Accepted {request_id}

    Celery->>DB: Get available userbot
    Celery->>Userbot: Connect via Telethon
    Userbot->>BotFather: /newbot
    BotFather-->>Userbot: Enter bot name
    Userbot->>BotFather: {bot_name}
    BotFather-->>Userbot: Enter username
    Userbot->>BotFather: {generated_username}
    BotFather-->>Userbot: Bot token

    Celery->>DB: Update BotCreationRequest (COMPLETED)
    Celery->>DB: Create TelegramBot
    Celery->>TelegramAPI: setWebhook()

    loop Polling
        Client->>API: GET /creation-status/{request_id}/
        API->>DB: Get BotCreationRequest
        API-->>Client: {status: completed, bot_username}
    end
```

### Обработка сообщения (Message Flow)

```mermaid
sequenceDiagram
    participant User
    participant Telegram
    participant Webhook
    participant Service
    participant AI
    participant Cache
    participant DB

    User->>Telegram: Send message
    Telegram->>Webhook: POST /webhook/{org_id}/

    Webhook->>Webhook: Verify secret token
    Webhook->>DB: Get/Create BotChat
    Webhook->>DB: Save BotMessage (user)

    Webhook->>Service: TelegramBotService.process_webhook_update()

    Service->>DB: Check subscription active
    alt Subscription expired
        Service->>DB: Disable AI on bots
        Service-->>Telegram: "AI отключен"
    else Subscription active
        Service->>DB: Get chat history (last 5 messages)
        Service->>Telegram: sendChatAction(typing)

        Service->>AI: BotAssistantService.get_response()
        AI->>Cache: Check response cache
        alt Cache hit
            Cache-->>AI: Cached response
        else Cache miss
            AI->>AI: Build system prompt
            AI->>AI: Call OpenAI proxy
            AI->>Cache: Cache response
        end
        AI-->>Service: AI response

        Service->>Service: Parse products from response
        alt Has products (> 3)
            Service->>Celery: send_telegram_products_task.delay()
        else Simple response
            Service->>Telegram: sendMessage()
        end

        Service->>DB: Save BotMessage (assistant)
    end
```

## Интеграции

### Telegram Bot API

| Метод | Использование |
|-------|---------------|
| `getMe` | Валидация токена, получение username |
| `setWebhook` | Установка webhook URL |
| `sendMessage` | Отправка текста |
| `sendPhoto` | Отправка изображений товаров |
| `editMessageText` | Обновление inline keyboards |
| `answerCallbackQuery` | Ответ на нажатие кнопок |
| `sendChatAction` | Индикатор набора текста |

### OpenAI API (через прокси)

```python
# Конфигурация
AI_ASSISTANT_URL = "http://161.35.153.151:8080"
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1500
TEMPERATURE = 0.5
```

**Структура промпта:**
1. Language detection rule
2. Identity (assistant name, position, gender)
3. Formatting rules (no markdown, ###NEXT### separator)
4. Logic scenarios (A: discounts, B: products, C: contacts, D: general)
5. Organization data (phones, address, hours)
6. Knowledge base (Q&A pairs)
7. Product catalog

### WAHA (WhatsApp)

| Endpoint | Использование |
|----------|---------------|
| `POST /api/sessions/{name}/start` | Запуск сессии |
| `GET /api/sessions/{name}/qr` | Получение QR-кода |
| `POST /api/sendText` | Отправка сообщения |
| `POST /api/sendSeen` | Отметка прочитано |

## Кеширование

### Response Cache

```python
# Ключ кеша ответов
cache_key = f"ai_response:{org_id}:{question_hash}"
timeout = 3600  # 1 час

# Правила кеширования
- Cache immediately: common patterns (hello, contacts, hours)
- Cache if per-org frequency >= 3
- Cache if global frequency >= 20
- Don't cache: responses with products (prices change)
```

### Training Data Cache

```python
# Celery task: cache_assistant_training_data
# Запуск: каждые 20 минут
# Timeout: 25 минут

cache_key = f"bot_training_data:{org_id}"
# Содержит:
# - Q&A pairs
# - Loaded file contents
# - Formatted catalog JSON
```

## Конфигурация

### Переменные окружения

| Переменная | Описание |
|------------|----------|
| `OPENAI_API_KEY` | API ключ OpenAI |
| `AI_ASSISTANT_URL` | URL прокси для OpenAI |
| `WAHA_BASE_URL` | URL WAHA сервера |
| `WAHA_API_KEY` | API ключ WAHA |
| `WAHA_WEBHOOK_SECRET` | Secret для HMAC проверки |
| `BACKEND_URL` | URL бэкенда для webhooks |

### Celery Queues

```python
CELERY_TASK_ROUTES = {
    'messenger_bots.tasks.*': {'queue': 'messenger_bots'},
    'messenger_bots.tasks.create_telegram_bot_task': {'queue': 'messenger_bots'},
    'messenger_bots.tasks.process_whatsapp_message_task': {'queue': 'messenger_bots'},
}
```

## Безопасность

### Webhook Verification

**Telegram:**
```python
secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
if secret_token != telegram_bot.webhook_secret:
    return HttpResponse(status=403)
```

**WAHA:**
```python
signature = request.headers.get("X-Webhook-Hmac-Sha512")
expected = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
if not hmac.compare_digest(expected, signature):
    return HttpResponse(status=403)
```

### Rate Limiting

| Ограничение | Значение |
|-------------|----------|
| Bots per userbot per day | 20 |
| Message delay | 0.5 сек |
| Products per page | 3 |
| Chat history limit | 5 пар сообщений |

## Мониторинг

### Логирование

```python
# Префиксы логов
[TG] - Telegram операции
[WA] - WhatsApp операции
[AI] - AI операции
[BOT_FACTORY] - Создание ботов
[SUB_CHECK] - Проверка подписок
[AUTO_CREATE] - Автосоздание ботов
```

### Метрики AI

```python
BotAssistantService.get_metrics(org_id=None)
# Returns:
# - total_requests
# - cache_hits
# - cache_hit_rate
# - errors
# - error_rate
# - avg_response_time_ms
```

## Расширение системы

### Добавление нового провайдера WhatsApp

1. Создать класс, реализующий `WhatsAppServiceInterface`
2. Добавить в `WhatsAppServiceFactory`
3. Добавить поля в модель `WhatsAppBot`

### Добавление нового платежного провайдера

1. Создать сервис в `organizations/services/`
2. Добавить модель конфигурации
3. Добавить webhook endpoint
4. Обновить `TransactionService`
