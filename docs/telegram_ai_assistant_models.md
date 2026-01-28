# Модели данных: Telegram AI-ассистент

## ER Диаграмма

```mermaid
erDiagram
    User ||--o{ Organization : owns
    User ||--o{ Membership : has
    User ||--o{ UserOrgSubscription : purchases

    Organization ||--o| TelegramBot : has
    Organization ||--o| WhatsAppBot : has
    Organization ||--o| Assistant : has
    Organization ||--o{ BotChat : has
    Organization ||--o{ BotCreationRequest : requests
    Organization ||--o{ UserOrgSubscription : receives

    TelegramBot ||--o{ BotChat : receives
    WhatsAppBot ||--o{ BotChat : receives

    BotChat ||--o{ BotMessage : contains
    BotChat |o--o| Chat : links_to

    Assistant ||--o{ Answer : has
    Assistant ||--o{ Chat : has
    Assistant ||--o{ UserAssistant : purchased_by

    Question ||--o{ Answer : answered_by
    Answer }o--o{ AnswerFile : has

    Chat ||--o{ ChatMessage : contains

    RegionalTariff ||--o{ UserOrgSubscription : used_in
    Country ||--o{ RegionalTariff : defines

    TelegramUserbot ||--o{ BotCreationRequest : creates

    User {
        int id PK
        string phone_number UK
        string full_name
        string email
        file avatar FK
        boolean is_new_user
    }

    Organization {
        int id PK
        int owner_id FK
        string title
        string address
        boolean is_active
        boolean payment_systems_activated
    }

    TelegramBot {
        int id PK
        int organization_id FK UK
        string bot_token
        string bot_username
        string webhook_secret
        string webhook_url
        boolean is_active
        boolean is_ai_enabled
        string last_error
        int context_messages_limit
    }

    WhatsAppBot {
        int id PK
        int organization_id FK UK
        string provider
        string waha_session_name
        string session_status
        string connected_phone_number
        boolean is_active
        boolean is_ai_enabled
    }

    BotChat {
        int id PK
        int organization_id FK
        string platform
        string platform_chat_id
        string user_name
        string user_phone
        string user_photo
        boolean is_active
        datetime last_message_at
    }

    BotMessage {
        int id PK
        int chat_id FK
        string sender
        text text
        string platform_message_id
        boolean is_read
        datetime created_at
    }

    BotCreationRequest {
        int id PK
        int organization_id FK
        int requested_by_id FK
        int userbot_used_id FK
        string status
        string bot_name
        string bot_username
        string bot_token
        string error_message
        datetime completed_at
    }

    TelegramUserbot {
        int id PK
        string phone_number UK
        string api_id
        string api_hash
        string session_string
        boolean is_authenticated
        string auth_state
        int bots_created_today
        int total_bots_created
    }

    Assistant {
        int id PK
        int organization_id FK UK
        string name
        string gender
        string position
        file image FK
        boolean is_enabled
    }

    Question {
        int id PK
        string text
        int ordering
    }

    Answer {
        int id PK
        int assistant_id FK
        int question_id FK
        text text
    }

    AnswerFile {
        int id PK
        file file
        int order
    }

    Chat {
        int id PK
        int user_id FK
        int assistant_id FK
        int bot_chat_id FK
        string source
        int unread_count
        boolean is_read
    }

    ChatMessage {
        int id PK
        int chat_id FK
        int parent_id FK
        string sender
        text text
        boolean is_read
    }

    UserOrgSubscription {
        int id PK
        int user_id FK
        int organization_id FK
        int tariff_id FK
        int transaction_id FK
        boolean is_active
        datetime active_until
    }

    RegionalTariff {
        int id PK
        int country_id FK
        string name
        decimal total_price
        int duration_days
    }

    Country {
        string code PK
        string name
        int currency_id FK
    }

    UserAssistant {
        int id PK
        int user_id FK
        int assistant_id FK
        int plan_id FK
        int transaction_id FK
        boolean is_active
        datetime active_until
    }

    Plan {
        int id PK
        string name
        decimal price
        string currency
        int duration_days
    }
```

## Детальное описание моделей

### 1. TelegramBot

**Файл:** `messenger_bots/models.py`

**Описание:** Конфигурация Telegram бота организации.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| organization | OneToOneField | No | Связь с Organization (CASCADE) |
| bot_token | CharField(100) | No | Токен от BotFather |
| bot_username | CharField(100) | Yes | Username бота (без @) |
| webhook_secret | CharField(64) | No | Secret для верификации webhook |
| webhook_url | URLField | Yes | URL установленного webhook |
| is_active | BooleanField | No | Активен ли бот (default: True) |
| is_ai_enabled | BooleanField | No | Включен ли AI (default: True) |
| last_error | TextField | Yes | Последняя ошибка API |
| context_messages_limit | IntegerField | No | Лимит истории для AI (default: 5) |
| created_at | DateTimeField | No | Дата создания |
| updated_at | DateTimeField | No | Дата обновления |

**Индексы:**
- `organization_id` (UNIQUE)

**Генерация webhook_secret:**
```python
def save(self, *args, **kwargs):
    if not self.webhook_secret:
        self.webhook_secret = secrets.token_urlsafe(32)
    super().save(*args, **kwargs)
```

---

### 2. WhatsAppBot

**Файл:** `messenger_bots/models.py`

**Описание:** Конфигурация WhatsApp бота организации.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| organization | OneToOneField | No | Связь с Organization (CASCADE) |
| provider | CharField(20) | No | Провайдер: waha/twilio/meta_cloud |
| waha_session_name | CharField(100) | Yes | Имя сессии WAHA |
| session_status | CharField(20) | No | Статус сессии |
| connected_phone_number | CharField(20) | Yes | Подключенный номер |
| phone_number_id | CharField(50) | Yes | Meta Cloud API |
| business_account_id | CharField(50) | Yes | Meta Cloud API |
| access_token | TextField | Yes | Meta Cloud API token |
| verify_token | CharField(100) | Yes | Webhook verification |
| webhook_secret | CharField(64) | Yes | HMAC secret |
| twilio_phone_number | CharField(20) | Yes | Twilio номер |
| is_active | BooleanField | No | Активен ли (default: True) |
| is_ai_enabled | BooleanField | No | Включен ли AI (default: True) |
| last_error | TextField | Yes | Последняя ошибка |
| last_activity_at | DateTimeField | Yes | Последняя активность |
| previous_phone_number | CharField(20) | Yes | Предыдущий номер (rebind) |
| phone_changed_at | DateTimeField | Yes | Дата смены номера |

**Статусы сессии (WhatsAppSessionStatus):**
| Статус | Описание |
|--------|----------|
| `pending` | Ожидание запуска |
| `scan_qr` | Ожидание сканирования QR |
| `authenticated` | Подключен |
| `disconnected` | Отключен |
| `failed` | Ошибка |

**Провайдеры (WhatsAppProvider):**
| Провайдер | Описание |
|-----------|----------|
| `waha` | Self-hosted WAHA |
| `twilio` | Twilio WhatsApp |
| `meta_cloud` | Meta Cloud API |

**Property `is_connected`:**
```python
@property
def is_connected(self) -> bool:
    if self.provider == WhatsAppProvider.WAHA:
        return self.session_status == WhatsAppSessionStatus.AUTHENTICATED
    elif self.provider == WhatsAppProvider.META_CLOUD:
        return bool(self.phone_number_id and self.access_token)
    return False
```

---

### 3. BotChat

**Файл:** `messenger_bots/models.py`

**Описание:** Чат с пользователем в боте.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| organization | ForeignKey | No | Связь с Organization (CASCADE) |
| platform | CharField(20) | No | Платформа: telegram/whatsapp |
| platform_chat_id | CharField(100) | No | ID чата в платформе |
| platform_user_id | CharField(100) | Yes | ID пользователя |
| user_name | CharField(255) | Yes | Имя пользователя |
| user_phone | CharField(20) | Yes | Телефон |
| user_photo | URLField | Yes | URL фото профиля |
| is_active | BooleanField | No | Активен ли (default: True) |
| last_message_at | DateTimeField | Yes | Время последнего сообщения |
| created_at | DateTimeField | No | Дата создания |
| updated_at | DateTimeField | No | Дата обновления |

**Constraints:**
```python
class Meta:
    unique_together = ("organization", "platform", "platform_chat_id")
```

**Платформы (BotPlatform):**
| Платформа | Значение |
|-----------|----------|
| Telegram | `telegram` |
| WhatsApp | `whatsapp` |

---

### 4. BotMessage

**Файл:** `messenger_bots/models.py`

**Описание:** Сообщение в чате бота.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| chat | ForeignKey | No | Связь с BotChat (CASCADE) |
| sender | CharField(20) | No | Отправитель: user/assistant |
| text | TextField | No | Текст сообщения |
| platform_message_id | CharField(100) | Yes | ID в платформе |
| is_read | BooleanField | No | Прочитано (default: False) |
| created_at | DateTimeField | No | Дата создания |

**Типы отправителей:**
| Sender | Описание |
|--------|----------|
| `user` | Сообщение от пользователя |
| `assistant` | Ответ AI-ассистента |

---

### 5. BotCreationRequest

**Файл:** `messenger_bots/models.py`

**Описание:** Запрос на автоматическое создание бота.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| organization | ForeignKey | No | Организация (CASCADE) |
| requested_by | ForeignKey | No | Кто запросил (SET_NULL) |
| status | CharField(20) | No | Статус создания |
| bot_name | CharField(64) | No | Имя бота |
| bot_username | CharField(100) | Yes | Username (после создания) |
| bot_token | CharField(100) | Yes | Токен (после создания) |
| userbot_used | ForeignKey | Yes | Использованный userbot |
| error_message | TextField | Yes | Сообщение об ошибке |
| base_url | URLField | Yes | URL для webhook |
| completed_at | DateTimeField | Yes | Дата завершения |
| created_at | DateTimeField | No | Дата создания |

**Статусы (BotCreationStatus):**
| Статус | Описание |
|--------|----------|
| `pending` | Ожидает обработки |
| `in_progress` | В процессе создания |
| `completed` | Успешно создан |
| `failed` | Ошибка |

---

### 6. TelegramUserbot

**Файл:** `messenger_bots/models.py`

**Описание:** Telegram userbot для создания ботов через BotFather.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| phone_number | CharField(20) | No | Номер телефона (unique) |
| api_id | CharField(20) | No | API ID от my.telegram.org |
| api_hash | CharField(64) | No | API Hash |
| session_string | TextField | Yes | Telethon session string |
| is_active | BooleanField | No | Активен (default: True) |
| is_authenticated | BooleanField | No | Авторизован |
| auth_state | CharField(20) | No | Состояние авторизации |
| phone_code_hash | CharField(100) | Yes | Hash для верификации кода |
| auth_state_message | TextField | Yes | Сообщение о состоянии |
| bots_created_today | IntegerField | No | Создано сегодня (default: 0) |
| total_bots_created | IntegerField | No | Всего создано (default: 0) |
| last_used_at | DateTimeField | Yes | Последнее использование |
| last_error | TextField | Yes | Последняя ошибка |

**Состояния авторизации (UserbotAuthState):**
| Состояние | Описание |
|-----------|----------|
| `not_started` | Не начата |
| `code_sent` | Код отправлен |
| `awaiting_2fa` | Ожидание 2FA |
| `authenticated` | Авторизован |
| `error` | Ошибка |

**Ограничения:**
- Максимум 20 ботов в день на userbot
- Счетчик сбрасывается в полночь (reset_userbot_daily_counters task)

---

### 7. Assistant

**Файл:** `organizations/models.py`

**Описание:** AI-ассистент организации.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| organization | OneToOneField | No | Организация (CASCADE) |
| name | CharField(255) | No | Имя ассистента |
| gender | CharField(20) | No | Пол: male/female |
| position | CharField(255) | No | Должность |
| image | ForeignKey | Yes | Фото (SET_NULL) |
| is_enabled | BooleanField | No | Включен (default: True) |
| created_at | DateTimeField | No | Дата создания |
| updated_at | DateTimeField | No | Дата обновления |

**Сигналы:**
```python
@receiver(post_save, sender=Assistant)
def invalidate_cache_on_assistant_save(sender, instance, **kwargs):
    invalidate_assistant_cache(instance.organization_id)
```

---

### 8. Answer

**Файл:** `organizations/models.py`

**Описание:** Ответ на вопрос в базе знаний.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| assistant | ForeignKey | No | Ассистент (CASCADE) |
| question | ForeignKey | No | Вопрос (CASCADE) |
| text | CharField(5000) | Yes | Текст ответа |
| files | ManyToManyField | Yes | Прикрепленные файлы |
| created_at | DateTimeField | No | Дата создания |
| updated_at | DateTimeField | No | Дата обновления |

**Сигналы:**
```python
@receiver(post_save, sender=Answer)
def invalidate_cache_on_answer_save(sender, instance, created, **kwargs):
    invalidate_assistant_cache(instance.assistant.organization_id)

@receiver(post_delete, sender=Answer)
def invalidate_cache_on_answer_delete(sender, instance, **kwargs):
    invalidate_assistant_cache(instance.assistant.organization_id)
```

---

### 9. UserOrgSubscription

**Файл:** `organizations/models.py`

**Описание:** Подписка организации на тарифный план.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| user | ForeignKey | No | Покупатель (CASCADE) |
| organization | ForeignKey | No | Организация (CASCADE) |
| tariff | ForeignKey | No | Тариф (PROTECT) |
| transaction | ForeignKey | Yes | Транзакция оплаты (SET_NULL) |
| is_active | BooleanField | No | Активна (default: True) |
| active_until | DateTimeField | Yes | Активна до |
| created_at | DateTimeField | No | Дата создания |
| updated_at | DateTimeField | No | Дата обновления |

**Использование в check_subscription_active:**
```python
subscription = (
    UserOrgSubscription.objects
    .filter(organization=organization, is_active=True)
    .order_by('-active_until')
    .first()
)
```

---

### 10. RegionalTariff

**Файл:** `organizations/models.py`

**Описание:** Региональный тарифный план.

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| country | ForeignKey | No | Страна (CASCADE) |
| name | CharField(50) | No | Название: starter/standard/profitable |
| display_name | CharField(100) | No | Отображаемое название |
| total_price | DecimalField | No | Полная цена |
| duration_days | IntegerField | No | Длительность в днях |
| features | JSONField | Yes | Список функций |
| is_active | BooleanField | No | Активен (default: True) |

---

### 11. Chat (Organizations)

**Файл:** `organizations/models.py`

**Описание:** Чат с AI-ассистентом (web и bot unified).

| Поле | Тип | Null | Описание |
|------|-----|------|----------|
| id | AutoField | No | Primary key |
| user | ForeignKey | Yes | Пользователь (CASCADE) |
| assistant | ForeignKey | No | Ассистент (CASCADE) |
| chat_by_org_user | BooleanField | No | От имени организации |
| source | CharField(20) | No | Источник: web/telegram/whatsapp |
| bot_chat | OneToOneField | Yes | Связь с BotChat (CASCADE) |
| unread_count | PositiveIntegerField | No | Непрочитанных (default: 0) |
| is_read | BooleanField | No | Прочитан (default: True) |
| created_at | DateTimeField | No | Дата создания |
| updated_at | DateTimeField | No | Дата обновления |

**Constraints:**
```python
class Meta:
    constraints = [
        UniqueConstraint(
            fields=["user", "assistant"],
            condition=Q(source="web"),
            name="unique_web_chat_per_user_assistant"
        ),
        UniqueConstraint(
            fields=["bot_chat"],
            condition=Q(bot_chat__isnull=False),
            name="unique_bot_chat_link"
        ),
    ]
```

**Источники (ChatSource):**
| Источник | Описание |
|----------|----------|
| `web` | Web-интерфейс |
| `telegram` | Telegram бот |
| `whatsapp` | WhatsApp бот |

---

## Связи между моделями

### Диаграмма связей

```
Organization ─────────────────────────────────────────┐
    │                                                 │
    ├── TelegramBot (1:1)                            │
    │       │                                         │
    │       └── BotChat (1:N) ──── BotMessage (1:N)  │
    │               │                                 │
    │               └── Chat (1:1, optional)         │
    │                                                 │
    ├── WhatsAppBot (1:1)                            │
    │       │                                         │
    │       └── BotChat (1:N) ──── BotMessage (1:N)  │
    │               │                                 │
    │               └── Chat (1:1, optional)         │
    │                                                 │
    ├── Assistant (1:1)                              │
    │       │                                         │
    │       ├── Answer (1:N) ──── Question (N:1)     │
    │       │       │                                 │
    │       │       └── AnswerFile (M:N)             │
    │       │                                         │
    │       ├── Chat (1:N) ──── ChatMessage (1:N)    │
    │       │                                         │
    │       └── UserAssistant (1:N)                  │
    │               │                                 │
    │               └── Plan (N:1)                   │
    │                                                 │
    ├── BotCreationRequest (1:N)                     │
    │       │                                         │
    │       └── TelegramUserbot (N:1)                │
    │                                                 │
    └── UserOrgSubscription (1:N)                    │
            │                                         │
            └── RegionalTariff (N:1)                 │
                    │                                 │
                    └── Country (N:1)                │
```

### Каскадное удаление

| Родитель | Дочерние (CASCADE) |
|----------|-------------------|
| Organization | TelegramBot, WhatsAppBot, Assistant, BotChat, BotCreationRequest |
| TelegramBot | (нет прямых дочерних) |
| BotChat | BotMessage, Chat (linked) |
| Assistant | Answer, Chat |
| Answer | (M2M files не удаляются) |
| Chat | ChatMessage |

### Защищенные связи (PROTECT)

| Поле | Модель | Причина |
|------|--------|---------|
| tariff | UserOrgSubscription | Нельзя удалить тариф с подписками |
| question | Answer | Нельзя удалить вопрос с ответами |
| role | Membership | Нельзя удалить роль с членствами |

---

## Миграции

### Ключевые миграции для messenger_bots

1. `0001_initial.py` - Создание TelegramBot, BotChat, BotMessage
2. `0015_whatsappbot.py` - Добавление WhatsApp
3. `0025_telegramuserbot.py` - Добавление userbots
4. `0030_botcreationrequest.py` - Автосоздание ботов
5. `0035_telegrambot_context_messages_limit.py` - Настройка контекста AI

### Ключевые миграции для organizations

1. `0001_initial.py` - Organization, Membership, Role
2. `0050_assistant.py` - AI-ассистент
3. `0055_answer_question.py` - База знаний
4. `0060_userorgsubscription.py` - Подписки организаций
5. `0065_chat_source.py` - Unified chats (web + bots)
