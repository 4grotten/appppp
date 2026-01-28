# Каталог ошибок: Telegram AI-ассистент

## Обзор

Документ описывает все возможные ошибки системы, их причины, HTTP коды и рекомендуемые действия.

## Структура ошибки

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {
    "field": ["Field-specific errors"]
  }
}
```

---

## 1. Ошибки аутентификации

### AUTH_001: Unauthorized

| Параметр | Значение |
|----------|----------|
| HTTP код | 401 |
| Сообщение | "Authentication credentials were not provided" |
| Причина | Отсутствует или невалидный токен |
| Решение | Добавить заголовок `Authorization: Token {token}` |

**Пример ответа:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### AUTH_002: Invalid Token

| Параметр | Значение |
|----------|----------|
| HTTP код | 401 |
| Сообщение | "Invalid token" |
| Причина | Токен истек или отозван |
| Решение | Получить новый токен через `/login/` |

### AUTH_003: Token Expired

| Параметр | Значение |
|----------|----------|
| HTTP код | 401 |
| Сообщение | "Token has expired" |
| Причина | Истек срок действия токена |
| Решение | Повторная аутентификация |

---

## 2. Ошибки прав доступа

### PERM_001: Permission Denied

| Параметр | Значение |
|----------|----------|
| HTTP код | 403 |
| Сообщение | "Permission denied" / "No rights to edit organization" |
| Причина | Пользователь не владелец и не имеет прав |
| Решение | Проверить права пользователя на организацию |

**Условия проверки:**
```python
def user_can_edit_organization(organization, user):
    if organization.owner == user:
        return True
    membership = Membership.objects.filter(
        organization=organization,
        user=user,
        role__can_edit_organization=True
    ).first()
    return membership is not None
```

### PERM_002: Webhook Secret Invalid

| Параметр | Значение |
|----------|----------|
| HTTP код | 403 |
| Сообщение | (пустой ответ) |
| Причина | Неверный X-Telegram-Bot-Api-Secret-Token |
| Решение | Проверить настройки webhook в Telegram |

### PERM_003: WAHA Signature Invalid

| Параметр | Значение |
|----------|----------|
| HTTP код | 403 |
| Сообщение | (пустой ответ) |
| Причина | Неверная HMAC подпись в X-Webhook-Hmac-Sha512 |
| Решение | Проверить WAHA_WEBHOOK_SECRET в настройках |

---

## 3. Ошибки валидации

### VAL_001: Invalid Bot Token Format

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Invalid bot token format. Token should be in format: 123456789:ABCdefGHI..." |
| Причина | Токен не содержит ":" |
| Решение | Получить корректный токен от @BotFather |

**Валидация:**
```python
def validate_bot_token(value):
    if ":" not in value:
        raise ValidationError("Invalid bot token format...")
    return value
```

### VAL_002: Bot Token Verification Failed

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Failed to verify bot token" |
| Причина | Telegram API не принял токен (getMe failed) |
| Решение | Проверить токен, возможно бот удален |

### VAL_003: Required Field Missing

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "This field is required" |
| Причина | Обязательное поле не заполнено |
| Решение | Заполнить все обязательные поля |

**Пример:**
```json
{
  "bot_name": ["This field is required."]
}
```

### VAL_004: Invalid Phone Format

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Invalid phone number format" |
| Причина | Неверный формат номера телефона |
| Решение | Использовать E.164 формат: +79991234567 |

---

## 4. Ошибки ресурсов

### RES_001: Organization Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Organization not found" |
| Причина | Организация не существует или удалена |
| Решение | Проверить ID организации |

### RES_002: Bot Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Telegram bot not found for this organization" |
| Причина | Бот не создан или удален |
| Решение | Создать бота через POST /messenger-bots/telegram/{org_id}/ |

### RES_003: Assistant Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Assistant not found" |
| Причина | AI-ассистент не создан |
| Решение | Создать ассистента через POST /organizations/assistant/ |

### RES_004: Creation Request Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Request not found" |
| Причина | Запрос на создание бота не найден |
| Решение | Проверить request_id |

### RES_005: Chat Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Chat not found" |
| Причина | Чат не существует или нет доступа |
| Решение | Проверить chat_id и права доступа |

### RES_006: Tariff Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Tariff not found or not available for your region" |
| Причина | Тариф не существует или недоступен |
| Решение | Получить список тарифов через GET /organizations/tariffs/ |

---

## 5. Ошибки конфликтов

### CONF_001: Bot Already Exists

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Telegram bot already exists for this organization" |
| Причина | Бот уже создан |
| Решение | Удалить существующего бота или обновить его |

### CONF_002: Assistant Already Exists

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Assistant already exists for this organization" |
| Причина | Ассистент уже создан (OneToOne) |
| Решение | Обновить через PUT /organizations/assistant/{id}/ |

### CONF_003: Username Already Taken

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Bot username is already taken" |
| Причина | Username занят в Telegram |
| Решение | Автоматически добавляется suffix при auto-create |

---

## 6. Ошибки доступности

### AVAIL_001: No Available Userbots

| Параметр | Значение |
|----------|----------|
| HTTP код | 503 |
| Сообщение | "No available userbots to create bot" |
| Причина | Все userbots достигли лимита или недоступны |
| Решение | Повторить позже или добавить новый userbot |

**Условия доступности:**
```python
userbot = TelegramUserbot.objects.filter(
    is_active=True,
    is_authenticated=True,
    bots_created_today__lt=20
).order_by('bots_created_today').first()
```

### AVAIL_002: WAHA Not Connected

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "WhatsApp session is not connected" |
| Причина | WAHA сессия не авторизована |
| Решение | Отсканировать QR-код через /qr/ endpoint |

### AVAIL_003: AI Service Unavailable

| Параметр | Значение |
|----------|----------|
| HTTP код | 503 |
| Сообщение | "AI service is temporarily unavailable" |
| Причина | OpenAI proxy недоступен |
| Решение | Автоматический fallback на direct OpenAI |

---

## 7. Ошибки подписки

### SUB_001: Subscription Expired

| Параметр | Значение |
|----------|----------|
| HTTP код | 200 (webhook) / 402 (API) |
| Сообщение | "Subscription has expired" |
| Причина | Подписка организации истекла |
| Решение | Продлить подписку |

**Логика проверки:**
```python
def check_subscription_active(organization):
    subscription = UserOrgSubscription.objects.filter(
        organization=organization,
        is_active=True
    ).order_by('-active_until').first()

    if not subscription:
        return False

    if subscription.active_until < timezone.now():
        subscription.is_active = False
        subscription.save()
        _disable_ai_for_organization(organization)
        return False

    return True
```

### SUB_002: No Active Subscription

| Параметр | Значение |
|----------|----------|
| HTTP код | 402 |
| Сообщение | "No active subscription found" |
| Причина | Организация никогда не покупала подписку |
| Решение | Купить подписку |

### SUB_003: AI Disabled by Subscription

| Параметр | Значение |
|----------|----------|
| HTTP код | N/A (бот не отвечает) |
| Сообщение | N/A |
| Причина | AI отключен из-за истекшей подписки |
| Решение | Продлить подписку, AI включится автоматически |

---

## 8. Ошибки создания бота

### BOT_001: Creation In Progress

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Bot creation is already in progress" |
| Причина | Запрос на создание уже существует |
| Решение | Дождаться завершения или отменить |

### BOT_002: Rate Limit Exceeded

| Параметр | Значение |
|----------|----------|
| HTTP код | 429 (внутренняя) |
| Сообщение | "Rate limit exceeded, retry in {seconds}" |
| Причина | Telegram ограничил создание ботов |
| Решение | Автоматический retry через 60 сек |

**Обработка:**
```python
@shared_task(max_retries=3, default_retry_delay=60)
def create_telegram_bot_task(request_id, base_url):
    try:
        result = BotFactoryService.create_bot_sync(...)
    except RateLimitError as e:
        raise self.retry(countdown=60)
```

### BOT_003: Username Generation Failed

| Параметр | Значение |
|----------|----------|
| HTTP код | N/A (async) |
| Сообщение | "Failed to generate unique username after 5 attempts" |
| Причина | Все варианты username заняты |
| Решение | Попробовать с другим именем бота |

### BOT_004: Webhook Setup Failed

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Failed to setup webhook" |
| Причина | Telegram отклонил установку webhook |
| Решение | Проверить доступность base_url |

---

## 9. Ошибки Telegram API

### TG_001: Unauthorized

| Параметр | Значение |
|----------|----------|
| Telegram код | 401 |
| Сообщение | "Unauthorized" |
| Причина | Невалидный bot_token |
| Решение | Получить новый токен у @BotFather |

### TG_002: Forbidden

| Параметр | Значение |
|----------|----------|
| Telegram код | 403 |
| Сообщение | "Forbidden: bot was blocked by the user" |
| Причина | Пользователь заблокировал бота |
| Решение | Пользователь должен разблокировать |

### TG_003: Chat Not Found

| Параметр | Значение |
|----------|----------|
| Telegram код | 400 |
| Сообщение | "Bad Request: chat not found" |
| Причина | Чат удален или бот исключен |
| Решение | Ожидать нового сообщения от пользователя |

### TG_004: Message Too Long

| Параметр | Значение |
|----------|----------|
| Telegram код | 400 |
| Сообщение | "Bad Request: message is too long" |
| Причина | Сообщение превышает 4096 символов |
| Решение | Разбить на части |

### TG_005: Rate Limit

| Параметр | Значение |
|----------|----------|
| Telegram код | 429 |
| Сообщение | "Too Many Requests: retry after {seconds}" |
| Причина | Слишком много запросов |
| Решение | Использовать MESSAGE_DELAY (0.5 сек) |

---

## 10. Ошибки платежей

### PAY_001: Payment Failed

| Параметр | Значение |
|----------|----------|
| HTTP код | 402 |
| Сообщение | "Payment failed" |
| Причина | Платеж отклонен провайдером |
| Решение | Повторить с другой картой |

### PAY_002: Invalid Amount

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Invalid payment amount" |
| Причина | Сумма меньше минимальной |
| Решение | Проверить минимальную сумму для провайдера |

### PAY_003: Promo Code Invalid

| Параметр | Значение |
|----------|----------|
| HTTP код | 400 |
| Сообщение | "Promo code not found or expired" |
| Причина | Промокод не существует или истек |
| Решение | Проверить код или продолжить без скидки |

### PAY_004: Transaction Not Found

| Параметр | Значение |
|----------|----------|
| HTTP код | 404 |
| Сообщение | "Transaction not found" |
| Причина | Транзакция не существует |
| Решение | Проверить transaction_id |

---

## 11. Ошибки AI

### AI_001: No Training Data

| Параметр | Значение |
|----------|----------|
| HTTP код | N/A (fallback message) |
| Сообщение | "К сожалению, я не могу ответить на ваш вопрос" |
| Причина | Нет данных для обучения AI |
| Решение | Заполнить базу знаний |

### AI_002: OpenAI Error

| Параметр | Значение |
|----------|----------|
| HTTP код | N/A (fallback message) |
| Сообщение | "Извините, произошла ошибка" |
| Причина | OpenAI вернул ошибку |
| Решение | Автоматический retry |

### AI_003: Context Too Long

| Параметр | Значение |
|----------|----------|
| HTTP код | N/A (truncate) |
| Сообщение | N/A |
| Причина | История чата слишком длинная |
| Решение | Автоматически обрезается до context_messages_limit |

---

## 12. Таблица всех кодов

| Код | HTTP | Категория | Описание |
|-----|------|-----------|----------|
| AUTH_001 | 401 | Auth | Нет токена |
| AUTH_002 | 401 | Auth | Невалидный токен |
| AUTH_003 | 401 | Auth | Токен истек |
| PERM_001 | 403 | Permission | Нет прав |
| PERM_002 | 403 | Permission | Неверный webhook secret |
| PERM_003 | 403 | Permission | Неверная WAHA подпись |
| VAL_001 | 400 | Validation | Неверный формат токена |
| VAL_002 | 400 | Validation | Токен не прошел проверку |
| VAL_003 | 400 | Validation | Отсутствует обязательное поле |
| VAL_004 | 400 | Validation | Неверный формат телефона |
| RES_001 | 404 | Resource | Организация не найдена |
| RES_002 | 404 | Resource | Бот не найден |
| RES_003 | 404 | Resource | Ассистент не найден |
| RES_004 | 404 | Resource | Запрос создания не найден |
| RES_005 | 404 | Resource | Чат не найден |
| RES_006 | 404 | Resource | Тариф не найден |
| CONF_001 | 400 | Conflict | Бот уже существует |
| CONF_002 | 400 | Conflict | Ассистент уже существует |
| CONF_003 | 400 | Conflict | Username занят |
| AVAIL_001 | 503 | Availability | Нет userbots |
| AVAIL_002 | 400 | Availability | WAHA не подключен |
| AVAIL_003 | 503 | Availability | AI недоступен |
| SUB_001 | 402 | Subscription | Подписка истекла |
| SUB_002 | 402 | Subscription | Нет подписки |
| BOT_001 | 400 | Bot Creation | Создание в процессе |
| BOT_002 | 429 | Bot Creation | Rate limit |
| BOT_003 | 500 | Bot Creation | Username не сгенерирован |
| BOT_004 | 400 | Bot Creation | Webhook не установлен |
| TG_001 | 401 | Telegram | Unauthorized |
| TG_002 | 403 | Telegram | Бот заблокирован |
| TG_003 | 400 | Telegram | Чат не найден |
| TG_004 | 400 | Telegram | Сообщение слишком длинное |
| TG_005 | 429 | Telegram | Rate limit |
| PAY_001 | 402 | Payment | Платеж отклонен |
| PAY_002 | 400 | Payment | Неверная сумма |
| PAY_003 | 400 | Payment | Промокод недействителен |
| PAY_004 | 404 | Payment | Транзакция не найдена |
| AI_001 | N/A | AI | Нет данных обучения |
| AI_002 | N/A | AI | Ошибка OpenAI |
| AI_003 | N/A | AI | Контекст слишком длинный |

---

## 13. Обработка ошибок в коде

### Middleware Exception Handler

```python
# common/middleware.py
class ExceptionHandlerMiddleware:
    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDeniedException):
            return JsonResponse(
                {"error": "permission_denied", "message": str(exception)},
                status=403
            )
        if isinstance(exception, ObjectNotFoundException):
            return JsonResponse(
                {"error": "not_found", "message": str(exception)},
                status=404
            )
        # ... other exceptions
```

### Telegram Error Handler

```python
# services/telegram.py
def _make_request(self, method: str, data: dict = None) -> dict:
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()

        if not result.get("ok"):
            error_code = result.get("error_code")
            description = result.get("description", "Unknown error")

            self.bot.last_error = f"{error_code}: {description}"
            self.bot.save(update_fields=["last_error"])

            logger.error(f"[TG] API error: {error_code} - {description}")
            return None

        return result.get("result")
    except requests.RequestException as e:
        self.bot.last_error = str(e)
        self.bot.save(update_fields=["last_error"])
        logger.exception(f"[TG] Request failed")
        return None
```

### AI Fallback Handler

```python
# services/assistant.py
def get_response(organization, question, ...):
    try:
        response = _call_ai_service(question, training_data, ...)
        return response
    except Exception as e:
        logger.exception(f"[AI] Error getting response")
        return _fallback_openai_response(question, training_data, ...)
```
