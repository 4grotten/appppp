# Пользовательские потоки: Telegram AI-ассистент

## Оглавление

1. [Покупка подписки](#1-покупка-подписки)
2. [Создание AI-ассистента](#2-создание-ai-ассистента)
3. [Автосоздание Telegram бота](#3-автосоздание-telegram-бота)
4. [Ручное подключение бота](#4-ручное-подключение-бота)
5. [Обработка входящего сообщения](#5-обработка-входящего-сообщения)
6. [Запрос товаров через бота](#6-запрос-товаров-через-бота)
7. [Настройка базы знаний](#7-настройка-базы-знаний)
8. [Управление подпиской](#8-управление-подпиской)

---

## 1. Покупка подписки

### Описание
Организация покупает тарифный план для активации функций AI-ассистента и автоматического создания Telegram бота.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Владелец организации
    participant Web as Web/Mobile App
    participant API as Backend API
    participant DB as PostgreSQL
    participant Payment as Payment Provider
    participant Celery as Celery Worker

    User->>Web: Выбор тарифа
    Web->>API: GET /organizations/tariffs/?country_code=RU
    API->>DB: RegionalTariff.objects.filter(country=...)
    DB-->>API: [Starter, Standard, Profitable]
    API-->>Web: Список тарифов с ценами

    User->>Web: Нажатие "Купить"
    Web->>API: POST /organizations/subscription/purchase/
    Note over Web,API: {organization_id, tariff_id, promocode?, utc_offset}

    API->>DB: Проверка существующей подписки
    API->>DB: Создание Transaction (status=PENDING)
    API->>DB: Создание UserOrgSubscription (is_active=false)

    alt Есть промокод
        API->>DB: PromoCode.objects.get(code=...)
        API->>API: Расчет скидки (discount_percent)
    end

    API-->>Web: {transaction_id, redirect_url}

    Web->>Payment: Redirect на страницу оплаты
    User->>Payment: Ввод данных карты
    Payment->>API: POST /transactions/result/{provider}/
    Note over Payment,API: Webhook с результатом

    API->>DB: Transaction.payment_status = ACCEPTED
    API->>DB: UserOrgSubscription.is_active = true
    API->>DB: UserOrgSubscription.active_until = now + duration_days

    alt План включает Telegram бот (id=5)
        API->>Celery: create_telegram_bot_task.delay()
    end

    API->>Celery: create_invoice_pdf.delay()
    Celery->>User: Email с квитанцией

    Payment-->>Web: Redirect на success_url
    Web-->>User: "Подписка активирована!"
```

### API Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/organizations/tariffs/` | Получить тарифы по региону |
| POST | `/organizations/subscription/purchase/` | Создать подписку |
| GET | `/organization/{id}/active-tariff/` | Проверить активную подписку |

### Валидации

1. **Проверка организации** - пользователь должен быть владельцем или иметь права
2. **Проверка тарифа** - тариф должен быть доступен для страны
3. **Проверка промокода** - если указан, должен быть валидным

### Возможные ошибки

| Код | Ошибка | Описание |
|-----|--------|----------|
| 400 | Invalid tariff | Тариф не найден или недоступен |
| 403 | Permission denied | Нет прав на организацию |
| 406 | Payment failed | Ошибка оплаты |

---

## 2. Создание AI-ассистента

### Описание
Создание и настройка AI-ассистента для организации (OneToOne связь).

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Владелец
    participant Web as Frontend
    participant API as Backend
    participant DB as PostgreSQL
    participant Cache as Redis

    User->>Web: Переход в раздел "AI-ассистент"
    Web->>API: GET /organizations/assistant/{assistant_id}/
    alt Ассистент существует
        API->>DB: Assistant.objects.get(organization=org)
        DB-->>API: Assistant object
        API-->>Web: {id, name, gender, position, is_enabled}
    else Ассистент не существует
        API-->>Web: 404 Not Found
    end

    User->>Web: Заполнение формы (имя, пол, должность)
    Web->>API: POST /organizations/assistant/
    Note over Web,API: {organization_id, name, gender, position, image_id?}

    API->>DB: Проверка: Assistant уже существует?
    alt Ассистент уже есть
        API-->>Web: 400 "Assistant already exists"
    else Создание нового
        API->>DB: Assistant.objects.create(...)
        DB-->>API: New Assistant
        API->>Cache: Invalidate training data cache
        API-->>Web: 201 Created {assistant}
    end

    User->>Web: Загрузка фото ассистента
    Web->>API: POST /files/
    API->>DB: Create File object
    API-->>Web: {file_id, url}

    Web->>API: PUT /organizations/assistant/{id}/
    Note over Web,API: {image_id: file_id}
    API->>DB: Update Assistant.image
    API-->>Web: 200 OK
```

### API Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/organizations/assistant/{id}/` | Получить ассистента |
| POST | `/organizations/assistant/` | Создать ассистента |
| PUT | `/organizations/assistant/{id}/` | Обновить ассистента |
| POST | `/organizations/assistant/toggle_assistant/` | Вкл/выкл ассистента |

### Поля ассистента

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| name | string | Да | Имя ассистента (до 255 символов) |
| gender | enum | Да | `male` или `female` |
| position | string | Да | Должность (до 255 символов) |
| image | file | Нет | Фото профиля |
| is_enabled | boolean | Нет | Активен ли (default: true) |

---

## 3. Автосоздание Telegram бота

### Описание
Автоматическое создание Telegram бота через BotFather с использованием Telethon userbot.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Владелец
    participant Web as Frontend
    participant API as Backend
    participant DB as PostgreSQL
    participant Celery as Celery Worker
    participant Userbot as Telethon Userbot
    participant BotFather as @BotFather
    participant TG as Telegram API

    User->>Web: Нажатие "Создать бота автоматически"
    Web->>API: POST /messenger-bots/telegram/auto-create/{org_id}/
    Note over Web,API: {bot_name: "Магазин Цветов"}

    API->>DB: Проверка: TelegramBot уже существует?
    alt Бот уже есть
        API-->>Web: 400 "Bot already exists"
    end

    API->>DB: Поиск доступного userbot
    Note over API,DB: is_authenticated=true, bots_created_today < 20

    alt Нет доступных userbots
        API-->>Web: 503 "No available userbots"
    end

    API->>DB: BotCreationRequest.create(status=PENDING)
    API->>Celery: create_telegram_bot_task.delay(request_id, base_url)
    API-->>Web: 202 {request_id, status: "pending"}

    loop Polling (каждые 2-3 сек)
        Web->>API: GET /messenger-bots/creation-status/{request_id}/
        API->>DB: BotCreationRequest.objects.get(id)
        API-->>Web: {status, bot_username?, error_message?}
    end

    Celery->>DB: Update status = IN_PROGRESS
    Celery->>DB: Get TelegramUserbot
    Celery->>Userbot: Connect via Telethon

    Userbot->>BotFather: /newbot
    BotFather-->>Userbot: "Alright, a new bot..."
    Userbot->>BotFather: {bot_name}
    BotFather-->>Userbot: "Good. Now let's choose a username..."

    Note over Userbot: Генерация username: {slug}_appofiz_bot

    Userbot->>BotFather: {generated_username}

    alt Username занят
        loop До 5 попыток
            Userbot->>Userbot: Добавить random suffix
            Userbot->>BotFather: {new_username}
        end
    end

    BotFather-->>Userbot: "Done! ... token: 123456:ABC..."

    Celery->>DB: Update BotCreationRequest (token, username)
    Celery->>DB: TelegramBot.objects.create(...)
    Celery->>DB: Userbot.bots_created_today += 1

    Celery->>TG: POST /bot{token}/setWebhook
    Note over Celery,TG: url={base_url}/api/v1/messenger-bots/telegram/webhook/{org_id}/

    TG-->>Celery: {"ok": true}

    Celery->>DB: Add bot link to org contacts
    Celery->>DB: Update status = COMPLETED

    Web->>API: GET /messenger-bots/creation-status/{request_id}/
    API-->>Web: {status: "completed", bot_username: "shop_flowers_appofiz_bot"}

    Web-->>User: "Бот создан! @shop_flowers_appofiz_bot"
```

### API Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/messenger-bots/telegram/auto-create/{org_id}/` | Запустить автосоздание |
| GET | `/messenger-bots/creation-status/{request_id}/` | Проверить статус |

### Статусы создания

| Статус | Описание |
|--------|----------|
| `pending` | Запрос создан, ожидает обработки |
| `in_progress` | Celery task выполняется |
| `completed` | Бот успешно создан |
| `failed` | Ошибка при создании |

### Ограничения

- **20 ботов/день** на один userbot
- **5 попыток** генерации username
- **60 сек retry** при rate limit от Telegram

---

## 4. Ручное подключение бота

### Описание
Подключение существующего Telegram бота с токеном от BotFather.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Владелец
    participant Web as Frontend
    participant API as Backend
    participant DB as PostgreSQL
    participant TG as Telegram API

    User->>BotFather: /newbot (вручную)
    BotFather-->>User: Token: 123456789:ABC...

    User->>Web: Ввод токена бота
    Web->>API: POST /messenger-bots/telegram/{org_id}/
    Note over Web,API: {bot_token: "123456789:ABC...", is_active: true}

    API->>API: Validate token format (contains ":")

    API->>TG: POST /bot{token}/getMe
    TG-->>API: {ok: true, result: {username: "my_bot"}}

    API->>DB: TelegramBot.update_or_create(...)
    Note over DB: bot_token, bot_username, is_active

    API->>TG: POST /bot{token}/setWebhook
    Note over API,TG: url=.../webhook/{org_id}/, secret_token=...

    TG-->>API: {ok: true}

    API->>DB: Update webhook_url

    API->>DB: Add @my_bot to org social contacts

    API-->>Web: 200 {id, bot_username, is_active, webhook_url}

    Web-->>User: "Бот @my_bot подключен!"
```

### Валидация токена

```python
def validate_bot_token(value):
    if ":" not in value:
        raise ValidationError(
            "Invalid bot token format. "
            "Token should be in format: 123456789:ABCdefGHI..."
        )
    return value
```

### Возможные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| Invalid token format | Токен без ":" | Проверить формат |
| Unauthorized | Неверный токен | Получить новый у BotFather |
| Bot not found | Бот удален | Создать нового бота |
| Webhook setup failed | Проблемы с Telegram API | Повторить позже |

---

## 5. Обработка входящего сообщения

### Описание
Полный цикл обработки сообщения от пользователя в Telegram боте.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant TGUser as Telegram User
    participant TG as Telegram API
    participant Webhook as Webhook Handler
    participant Service as TelegramBotService
    participant SubCheck as SubscriptionCheck
    participant AI as BotAssistantService
    participant OpenAI as OpenAI Proxy
    participant Cache as Redis Cache
    participant DB as PostgreSQL
    participant WS as WebSocket

    TGUser->>TG: Отправка сообщения
    TG->>Webhook: POST /webhook/{org_id}/
    Note over TG,Webhook: Headers: X-Telegram-Bot-Api-Secret-Token

    Webhook->>Webhook: Verify secret token
    alt Invalid token
        Webhook-->>TG: 403 Forbidden
    end

    Webhook->>DB: TelegramBot.objects.get(organization_id, is_active=True)
    Webhook->>Service: process_webhook_update(bot, update)

    Service->>Service: Detect language from user.language_code

    Service->>DB: BotChat.get_or_create(platform_chat_id)
    alt New chat
        Service->>TG: getUserProfilePhotos
        TG-->>Service: Photo URL
        Service->>DB: Update user_photo
    end

    Service->>DB: BotMessage.create(sender=USER, text=...)

    Service->>DB: Get/Create organizations.Chat (linked)
    Service->>DB: Chat.unread_count += 1

    Service->>WS: Send notification to org channel
    Note over Service,WS: {"type": "new_message", "chat_id": ...}

    alt Message is /start
        Service->>TG: sendMessage("Добро пожаловать!")
        Service->>TG: Send main menu keyboard
        Service-->>Webhook: "welcome"
    else Regular message
        Service->>DB: Check bot.is_ai_enabled
        alt AI disabled
            Service-->>Webhook: null (no response)
        end

        Service->>SubCheck: check_subscription_active(organization)
        SubCheck->>DB: UserOrgSubscription.filter(is_active=True)

        alt Subscription expired
            SubCheck->>DB: subscription.is_active = False
            SubCheck->>DB: TelegramBot.is_ai_enabled = False
            SubCheck->>DB: WhatsAppBot.is_ai_enabled = False
            Service-->>Webhook: null
        end

        Service->>DB: Get chat history (last 5 pairs)
        Service->>TG: sendChatAction(typing)

        Service->>AI: get_response(org, question, history, language)

        AI->>Cache: Check ai_response:{org_id}:{hash}
        alt Cache hit
            Cache-->>AI: Cached response
        else Cache miss
            AI->>AI: _prepare_training_data()
            AI->>Cache: Get training_data:{org_id}
            AI->>AI: build_system_prompt(...)
            AI->>OpenAI: POST /bot/openai-proxy/
            OpenAI-->>AI: {answer: "..."}
            AI->>Cache: Set ai_response (if cacheable)
        end

        AI-->>Service: AI response text

        Service->>Service: parse_products_from_response()

        alt Has products (> PRODUCTS_PER_PAGE)
            Service->>Cache: Store products for pagination
            Service->>Celery: send_telegram_products_task.delay()
        else Simple response or <= 3 products
            loop For each product
                Service->>TG: sendMessage(product_text)
                Service->>DB: BotMessage.create(sender=ASSISTANT)
            end
        end

        Service->>TG: Send main menu keyboard
        Service-->>Webhook: "response sent"
    end

    Webhook-->>TG: 200 OK
```

### Ключевые проверки

1. **Secret Token** - Telegram передает токен в заголовке
2. **Bot Active** - Бот должен быть активен (`is_active=True`)
3. **AI Enabled** - AI должен быть включен (`is_ai_enabled=True`)
4. **Subscription Active** - Подписка не должна быть истекшей

### Кеширование ответов

```python
# Правила кеширования
COMMON_PATTERNS = ["привет", "hello", "контакты", "contacts", "часы работы"]

def should_cache(question, response):
    # 1. Common patterns - cache immediately
    if is_common_pattern(question):
        return True

    # 2. Per-org frequency >= 3
    org_freq = cache.incr(f"ai_freq:{org_id}:{hash}")
    if org_freq >= 3:
        return True

    # 3. Global frequency >= 20
    global_freq = cache.incr(f"ai_global_freq:{hash}")
    if global_freq >= 20:
        return True

    # 4. Don't cache if has products (prices change)
    if has_products(response):
        return False

    return False
```

---

## 6. Запрос товаров через бота

### Описание
Пользователь запрашивает товары, AI находит релевантные и отправляет с пагинацией.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Telegram User
    participant TG as Telegram API
    participant Service as TelegramBotService
    participant AI as BotAssistantService
    participant Celery as Celery Worker
    participant Cache as Redis
    participant DB as PostgreSQL

    User->>TG: "Покажи красные розы"
    TG->>Service: Webhook update

    Service->>AI: get_response("Покажи красные розы")

    AI->>AI: Build prompt with catalog
    Note over AI: SCENARIO B: Products requested

    AI->>AI: Call OpenAI
    Note over AI: System prompt includes product search rules

    AI-->>Service: "Вот что я нашел:\n\n" +
    Note over AI: "Товар: Розы красные\nЦена: 1500 ₽\nСсылка: https://...\n###NEXT###\n" +
    Note over AI: "Товар: Букет роз\nЦена: 3000 ₽\nСсылка: https://...\n###NEXT###\n" +
    Note over AI: "..." (всего 10 товаров)

    Service->>Service: parse_products_from_response()
    Note over Service: Split by ###NEXT### or regex

    Service->>Service: products = [10 items], footer = "Посмотреть все..."

    alt len(products) > PRODUCTS_PER_PAGE (3)
        Service->>Cache: cache_products(chat_id, products, footer)
        Note over Cache: Key: tg_products:{chat_id}, timeout: 600s

        Service->>Celery: send_telegram_products_task.delay(
        Note over Celery: bot_id, chat_id, products, footer, page=0)

        Celery->>DB: Get TelegramBot
        Celery->>TG: sendMessage(products[0])
        Celery->>TG: sendMessage(products[1])
        Celery->>TG: sendMessage(products[2])
        Note over Celery: Delay 0.5s between messages

        Celery->>TG: sendMessage("Показать еще?", keyboard)
        Note over TG: InlineKeyboard: [Показать еще ➡️]
    else
        Service->>TG: Send all products directly
    end

    User->>TG: Click "Показать еще"
    TG->>Service: callback_query: "more_products:1"

    Service->>TG: answerCallbackQuery()
    Service->>Cache: get_cached_products(chat_id)
    Cache-->>Service: (products, footer)

    Service->>Celery: send_telegram_products_task.delay(page=1)
    Celery->>TG: sendMessage(products[3])
    Celery->>TG: sendMessage(products[4])
    Celery->>TG: sendMessage(products[5])

    alt More pages available
        Celery->>TG: sendMessage("Показать еще?")
    else Last page
        Celery->>TG: sendMessage(footer)
        Celery->>TG: sendMessage("Главное меню", main_menu_keyboard)
    end
```

### Формат товара от AI

```
Товар: Розы красные премиум
Цена: 1 500 ₽
Ссылка: https://appofiz.com/shop/123/
###NEXT###
Товар: Букет "Романтика"
Цена: 3 000 ₽
Ссылка: https://appofiz.com/shop/456/
```

### Inline Keyboards

**Пагинация:**
```json
{
  "inline_keyboard": [[
    {"text": "Показать еще ➡️", "callback_data": "more_products:1"}
  ]]
}
```

**Главное меню:**
```json
{
  "inline_keyboard": [
    [{"text": "📦 Каталог", "callback_data": "catalog"}],
    [{"text": "📞 Контакты", "callback_data": "contacts"}]
  ]
}
```

---

## 7. Настройка базы знаний

### Описание
Добавление ответов на вопросы для обучения AI-ассистента.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Владелец
    participant Web as Frontend
    participant API as Backend
    participant DB as PostgreSQL
    participant Cache as Redis
    participant Celery as Celery Worker

    User->>Web: Переход в "База знаний"
    Web->>API: GET /organizations/assistant/questions/?organization_id=123

    API->>DB: Assistant.objects.get(organization_id=123)
    API->>DB: Question.objects.all().order_by("ordering")
    API->>DB: Answer.objects.filter(assistant=assistant)

    API-->>Web: [
    Note over Web: {id: 1, text: "Режим работы?", answer: null},
    Note over Web: {id: 2, text: "Способы доставки?", answer: {text: "..."}},
    Note over Web: ...]

    User->>Web: Выбор вопроса "Режим работы?"
    User->>Web: Ввод ответа + загрузка файла

    Web->>API: POST /organizations/assistant/questions/answer/file/
    Note over API: Upload file
    API->>DB: AnswerFile.objects.create()
    API-->>Web: {id: 456, file: "...", name: "schedule.pdf"}

    Web->>API: POST /organizations/assistant/questions/answer/
    Note over Web,API: {assistant_id, question_id, text: "...", file_ids: [456]}

    API->>DB: Answer.objects.create(...)
    API->>DB: answer.files.set([456])

    Note over API: Signal: post_save on Answer
    API->>Cache: Invalidate training_data:{org_id}

    API-->>Web: 201 Created {id, text, files}

    Note over Celery: Background: cache_assistant_training_data
    Celery->>DB: Get all Answers for Assistant
    Celery->>Celery: Load file contents (PDF, DOCX...)
    Celery->>Cache: Set training_data:{org_id}

    Web-->>User: "Ответ сохранен!"
```

### Стандартные вопросы

| ID | Вопрос |
|----|--------|
| 1 | Режим работы? |
| 2 | Способы доставки? |
| 3 | Способы оплаты? |
| 4 | Как сделать заказ? |
| 5 | Есть ли скидки? |
| 6 | Где вы находитесь? |
| 7 | Как связаться? |
| 8 | Есть ли гарантия? |
| 9 | Можно ли вернуть товар? |
| 10 | Другое (свободный ответ) |

### Поддерживаемые типы файлов

| Расширение | Обработка |
|------------|-----------|
| .pdf | pypdf / PyPDF2 / pdfplumber |
| .docx | python-docx |
| .txt | Plain text |
| .json | JSON catalog format |
| .csv | CSV parsing |
| .md | Markdown |

---

## 8. Управление подпиской

### Описание
Проверка статуса подписки и автоматическое отключение AI при истечении.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant Webhook as Telegram Webhook
    participant Service as TelegramBotService
    participant SubCheck as check_subscription_active
    participant DB as PostgreSQL
    participant Log as Logger

    Note over Webhook: Incoming message

    Webhook->>Service: process_webhook_update()

    Service->>SubCheck: check_subscription_active(organization)

    SubCheck->>DB: UserOrgSubscription.filter(organization, is_active=True)
    Note over SubCheck: .order_by('-active_until').first()

    alt No active subscription
        SubCheck->>Log: "[SUB_CHECK] No active subscription for org {id}"
        SubCheck-->>Service: False
    else Subscription found
        SubCheck->>SubCheck: Check active_until < now()

        alt Subscription expired
            SubCheck->>Log: "[SUB_CHECK] Subscription expired for org {id}"

            SubCheck->>DB: subscription.is_active = False
            SubCheck->>DB: subscription.save()

            SubCheck->>DB: TelegramBot.filter(org, is_ai_enabled=True)
            SubCheck->>DB: .update(is_ai_enabled=False)

            SubCheck->>DB: WhatsAppBot.filter(org, is_ai_enabled=True)
            SubCheck->>DB: .update(is_ai_enabled=False)

            SubCheck->>Log: "[SUB_CHECK] AI disabled for org {id}: TG={n}, WA={m}"

            SubCheck-->>Service: False
        else Subscription active
            SubCheck-->>Service: True
        end
    end

    alt Subscription check returned False
        Service-->>Webhook: null (no AI response)
    else Subscription active
        Service->>Service: Continue with AI response
    end
```

### Автоматические действия при истечении

1. **Деактивация подписки** - `is_active = False`
2. **Отключение Telegram AI** - `TelegramBot.is_ai_enabled = False`
3. **Отключение WhatsApp AI** - `WhatsAppBot.is_ai_enabled = False`
4. **Логирование** - Запись в лог с деталями

### Ручное продление

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB

    User->>API: POST /organizations/subscription/purchase/
    Note over API: {organization_id, tariff_id}

    API->>DB: Get existing subscription

    alt Existing active subscription
        API->>DB: active_until += duration_days
    else Expired or no subscription
        API->>DB: Create new subscription
        API->>DB: active_until = now + duration_days
    end

    API->>DB: TelegramBot.is_ai_enabled = True
    API->>DB: WhatsAppBot.is_ai_enabled = True

    API-->>User: {transaction_id, new_active_until}
```

---

## Приложение: Callback Data Format

| Callback | Формат | Описание |
|----------|--------|----------|
| catalog | `catalog` | Показать категории |
| contacts | `contacts` | Показать контакты |
| category | `cat_{id}` | Товары категории |
| product | `prod_{id}` | Детали товара |
| more | `more_products:{page}` | Пагинация |
| back | `back` | Назад в меню |
