# API Specification: Bot Settings Management

## Overview

API для мобильного приложения: управление настройками Telegram и WhatsApp ботов.

---

## 1. Изменения в моделях

### TelegramBot — новые поля
```python
is_ai_enabled = BooleanField(default=True)  # AI-ассистент вкл/выкл
```

### WhatsAppBot — новые поля
```python
is_ai_enabled = BooleanField(default=True)       # AI-ассистент вкл/выкл
previous_phone_number = CharField(max_length=20, null=True, blank=True)  # Предыдущий номер
phone_changed_at = DateTimeField(null=True, blank=True)  # Дата смены номера
```

---

## 2. Эндпоинты

### 2.1. Telegram Bot Settings

**URL:** `POST /api/bots/telegram/<org_id>/settings/`

Обновление имени, описания и/или аватарки бота через Telegram Bot API.

**Request (multipart/form-data):**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | No | max 64 chars |
| description | string | No | max 512 chars |
| photo | file | No | jpg/png, max 5MB |

**Response 200:**
```json
{
  "name": {"success": true},
  "description": {"success": true},
  "photo": {"success": true}
}
```
Каждое поле присутствует только если было отправлено в запросе.

**Response 400:**
```json
{"error": "No settings provided"}
```

**Response 502:**
```json
{"name": {"success": false, "error": "Telegram API error: ..."}}
```

---

**URL:** `DELETE /api/bots/telegram/<org_id>/settings/photo/`

Удаление аватарки бота.

**Response 200:**
```json
{"success": true}
```

---

### 2.2. Telegram AI Toggle

**URL:** `PATCH /api/bots/telegram/<org_id>/`

**Request:**
```json
{"is_ai_enabled": false}
```

**Response 200:**
```json
{"is_ai_enabled": false}
```

---

### 2.3. WhatsApp AI Toggle

**URL:** `PATCH /api/bots/whatsapp/waha/<org_id>/`

**Request:**
```json
{"is_ai_enabled": false}
```

**Response 200:**
```json
{"is_ai_enabled": false}
```

---

### 2.4. WhatsApp Phone Rebind (перепривязка номера)

**URL:** `POST /api/bots/whatsapp/waha/<org_id>/session/rebind/`

Перепривязка WhatsApp номера: останавливает текущую сессию, сохраняет старый номер, запускает новую сессию.

**Request:** пустой body

**Response 200:**
```json
{
  "success": true,
  "previous_phone_number": "+79991234567",
  "phone_changed_at": "2026-01-23T12:00:00Z",
  "session_status": "SCAN_QR",
  "qr_code": "base64..."
}
```

После этого фронт показывает QR для сканирования с нового телефона.

**Response 400:**
```json
{"error": "No phone number connected to rebind"}
```

---

### 2.5. Получение текущих настроек

**URL:** `GET /api/bots/telegram/<org_id>/` (существующий эндпоинт, дополняем)

**Response — добавляем поле:**
```json
{
  "...existing fields...",
  "is_ai_enabled": true
}
```

**URL:** `GET /api/bots/whatsapp/waha/<org_id>/` (существующий эндпоинт, дополняем)

**Response — добавляем поля:**
```json
{
  "...existing fields...",
  "is_ai_enabled": true,
  "previous_phone_number": null,
  "phone_changed_at": null
}
```

---

## 3. Бизнес-логика

### 3.1. Проверка is_ai_enabled

**Место вставки:**
- `telegram.py:_handle_message()` — после сохранения входящего сообщения, перед вызовом AI
- `tasks.py:process_whatsapp_message_task()` — после инициализации сервиса, перед вызовом AI

**Поведение при is_ai_enabled=False:**
- Входящее сообщение **сохраняется** в БД (видно в чатах)
- AI **не вызывается**, ответ не генерируется
- Для WhatsApp: сообщение **помечается как прочитанное** (blue checkmarks), но бот молчит

### 3.2. Проверка подписки при сообщении

**Логика:**
```python
from django.utils import timezone
from organizations.models import UserOrgSubscription

def check_subscription_active(organization) -> bool:
    """Проверяет, активна ли подписка организации."""
    subscription = (
        UserOrgSubscription.objects
        .filter(organization=organization, is_active=True)
        .order_by('-active_until')
        .first()
    )
    if not subscription:
        return False
    if subscription.active_until and subscription.active_until < timezone.now():
        # Подписка истекла — отключаем AI
        subscription.is_active = False
        subscription.save(update_fields=['is_active'])
        # Отключаем AI на ботах
        _disable_ai_for_organization(organization)
        return False
    return True

def _disable_ai_for_organization(organization):
    """Отключает AI для всех ботов организации."""
    TelegramBot.objects.filter(
        organization=organization, is_ai_enabled=True
    ).update(is_ai_enabled=False)
    WhatsAppBot.objects.filter(
        organization=organization, is_ai_enabled=True
    ).update(is_ai_enabled=False)
```

**Порядок проверок при входящем сообщении:**
1. Проверить `is_ai_enabled` на модели бота → если False, молчим
2. Проверить `active_until` подписки → если истекла, ставим `is_ai_enabled=False`, молчим
3. Вызвать AI

### 3.3. WhatsApp Rebind Flow

1. Проверяем, есть ли текущий `connected_phone_number`
2. Сохраняем `previous_phone_number = connected_phone_number`
3. Сохраняем `phone_changed_at = timezone.now()`
4. Вызываем `service.stop_session()`
5. Очищаем `connected_phone_number`
6. Обновляем `session_status = SCAN_QR`
7. Вызываем `service.start_session()`
8. Получаем QR: `service.get_qr_code()`
9. Возвращаем QR фронту

### 3.4. Telegram Settings через Bot API

Каждое действие — отдельный вызов к Telegram API:
- `setMyName`: `POST https://api.telegram.org/bot{token}/setMyName` с `{"name": "..."}`
- `setMyDescription`: `POST .../setMyDescription` с `{"description": "..."}`
- `setMyPhoto`: `POST .../setMyPhoto` с multipart file upload
- `deleteMyPhoto`: `POST .../deleteMyPhoto`

---

## 4. Permissions

Все эндпоинты требуют:
- Аутентификация (`IsAuthenticated`)
- Пользователь является владельцем организации

---

## 5. Чек-лист реализации

- [ ] Добавить `is_ai_enabled` в TelegramBot
- [ ] Добавить `is_ai_enabled`, `previous_phone_number`, `phone_changed_at` в WhatsAppBot
- [ ] Создать миграцию
- [ ] Создать `TelegramBotSettingsAPIView` (PATCH для name/description, POST для photo, DELETE для photo)
- [ ] Добавить PATCH с `is_ai_enabled` в существующие TelegramBotAPIView и WhatsAppWAHABotAPIView
- [ ] Создать `WhatsAppRebindAPIView` (POST для перепривязки)
- [ ] Создать сервис `TelegramBotSettingsService` (вызовы к Telegram API)
- [ ] Добавить проверку `is_ai_enabled` в telegram.py и tasks.py
- [ ] Добавить проверку подписки (`check_subscription_active`) в telegram.py и tasks.py
- [ ] Обновить сериализаторы для новых полей
- [ ] Добавить URL-маршруты
- [ ] Логирование всех операций
