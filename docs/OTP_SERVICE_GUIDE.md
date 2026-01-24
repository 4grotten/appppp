# OTP Bot Service — Полное руководство

## Содержание
1. [Деплой и настройка](#1-деплой-и-настройка)
2. [Использование API](#2-использование-api)
3. [Интеграция с Lovable.dev](#3-интеграция-с-lovabledev)
4. [Промпт для Lovable.dev](#4-промпт-для-lovabledev)

---

## 1. Деплой и настройка

### 1.1. Переменные окружения

Добавь в `.env` файл на сервере:

```env
# WAHA (уже должен быть настроен)
WAHA_BASE_URL=http://waha:3000
WAHA_API_KEY=your-waha-api-key

# OTP Bot
WAHA_OTP_SESSION_NAME=otp_service_bot
OTP_CODE_TTL_SECONDS=300
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_PER_PHONE_10MIN=3
OTP_ADMIN_API_KEY=сгенерируй-надёжный-ключ-тут
OTP_MESSAGE_TEMPLATE=Ваш код подтверждения: {code}\n\nКод действителен {ttl_minutes} мин. Не сообщайте его никому.
```

### 1.2. WAHA Plus

OTP бот использует отдельную сессию в WAHA Plus (мульти-сессия).
Убедись что WAHA Plus лицензия активна и инстанс запущен.

### 1.3. Применение миграций

```bash
cd /home/mioneris/appofiz/backend
python manage.py migrate otp_bot
```

### 1.4. Celery Beat (очистка просроченных кодов)

Добавь в настройки Celery Beat (или `CELERY_BEAT_SCHEDULE`):

```python
CELERY_BEAT_SCHEDULE = {
    ...
    'cleanup-expired-otp': {
        'task': 'otp_bot.tasks.cleanup_expired_otp_codes',
        'schedule': crontab(minute=0),  # Каждый час
    },
}
```

### 1.5. Первичная инициализация бота

После деплоя, один раз вызови:

```bash
curl -X POST https://api.apofiz.com/api/v1/otp-bot/initialize/ \
  -H "X-OTP-API-Key: твой-admin-ключ"
```

Затем получи QR и отсканируй с WhatsApp номера, выделенного под OTP:

```bash
curl https://api.apofiz.com/api/v1/otp-bot/qr/ \
  -H "X-OTP-API-Key: твой-admin-ключ"
```

Response:
```json
{"qr_code": "base64-data...", "message": "Scan QR with WhatsApp"}
```

Отобрази QR (base64 image) и отсканируй. После этого бот готов к отправке.

Проверь статус:
```bash
curl https://api.apofiz.com/api/v1/otp-bot/status/ \
  -H "X-OTP-API-Key: твой-admin-ключ"
```

Response при успехе:
```json
{
  "is_initialized": true,
  "status": "connected",
  "phone_number": "+77001234567",
  "session_name": "otp_service_bot"
}
```

---

## 2. Использование API

### 2.1. Отправка OTP

```
POST /api/v1/otp/send/
Content-Type: application/json

{"phone_number": "+79991234567"}
```

Response `200`:
```json
{
  "otp_id": "uuid-строка",
  "phone_number": "+79991234567",
  "expires_at": "2026-01-24T12:05:00+00:00",
  "sent": true
}
```

Ошибки:
| Status | Причина |
|--------|---------|
| 400 | Неверный формат номера |
| 429 | Rate limit (3 OTP за 10 мин) |
| 503 | Бот не подключён |

### 2.2. Верификация OTP

```
POST /api/v1/otp/verify/
Content-Type: application/json

{"phone_number": "+79991234567", "code": "482916"}
```

Response `200` (успех):
```json
{"is_valid": true, "error": null}
```

Response `200` (неудача):
```json
{"is_valid": false, "error": "Invalid code. 2 attempts remaining"}
```

Возможные ошибки в поле `error`:
- `"No active OTP found"` — нет активного кода (не отправляли или истёк)
- `"OTP expired"` — код протух (>5 мин)
- `"Max attempts exceeded"` — 3 попытки исчерпаны
- `"Invalid code. N attempts remaining"` — неверный код

### 2.3. Повторная отправка

```
POST /api/v1/otp/resend/
Content-Type: application/json

{"phone_number": "+79991234567"}
```

Response `200`: как у send.

Response `429` (cooldown):
```json
{"error": "Cooldown: wait 42 seconds", "seconds_remaining": 42}
```

### 2.4. Полный Flow

```
1. Пользователь вводит номер телефона
2. Фронт → POST /otp/send/ {phone_number}
3. Пользователь получает WhatsApp сообщение с 6-значным кодом
4. Пользователь вводит код в форму
5. Фронт → POST /otp/verify/ {phone_number, code}
6. Если is_valid=true → регистрация/вход подтверждён
7. Если is_valid=false → показать error, предложить "Отправить повторно"
8. Повторная отправка → POST /otp/resend/ {phone_number}
```

---

## 3. Интеграция с Lovable.dev

### 3.1. Base URL

```
https://api.apofiz.com/api/v1
```

### 3.2. Эндпоинты для фронта (без авторизации)

| Action | Method | URL | Body |
|--------|--------|-----|------|
| Отправить код | POST | `/otp/send/` | `{phone_number}` |
| Проверить код | POST | `/otp/verify/` | `{phone_number, code}` |
| Отправить повторно | POST | `/otp/resend/` | `{phone_number}` |

### 3.3. JavaScript примеры для Lovable

#### Отправка OTP:
```javascript
const sendOTP = async (phoneNumber) => {
  const response = await fetch('https://api.apofiz.com/api/v1/otp/send/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber })
  });

  if (response.status === 429) {
    const data = await response.json();
    throw new Error(data.error); // Rate limit
  }
  if (response.status === 503) {
    throw new Error('Сервис временно недоступен');
  }

  return await response.json();
};
```

#### Верификация:
```javascript
const verifyOTP = async (phoneNumber, code) => {
  const response = await fetch('https://api.apofiz.com/api/v1/otp/verify/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber, code })
  });

  const data = await response.json();
  return data; // { is_valid: true/false, error: "..." }
};
```

#### Повторная отправка:
```javascript
const resendOTP = async (phoneNumber) => {
  const response = await fetch('https://api.apofiz.com/api/v1/otp/resend/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber })
  });

  if (response.status === 429) {
    const data = await response.json();
    // data.seconds_remaining — секунд до следующей попытки
    return { cooldown: true, seconds: data.seconds_remaining };
  }

  return await response.json();
};
```

### 3.4. Формат номера телефона

Номер **обязательно** в формате E.164:
- Начинается с `+`
- Только цифры после `+`
- 7-15 цифр

Примеры:
- `+79991234567` (Россия)
- `+77001234567` (Казахстан)
- `+971501234567` (ОАЭ)

### 3.5. Обработка ошибок в UI

| HTTP Status | Что показать пользователю |
|-------------|--------------------------|
| 200 + `sent: true` | "Код отправлен на WhatsApp" |
| 200 + `is_valid: true` | Успех, переход далее |
| 200 + `is_valid: false` | Показать `error` из ответа |
| 400 | "Неверный формат номера" |
| 429 | "Слишком много попыток. Подождите N секунд" |
| 503 | "Сервис временно недоступен, попробуйте позже" |

---

## 4. Промпт для Lovable.dev

Скопируй и вставь в Lovable.dev при создании экранов регистрации/входа:

---

```
# WhatsApp OTP Verification Integration

## API Configuration
Base URL: https://api.apofiz.com/api/v1
No authentication required for OTP endpoints.

## Available Endpoints

### 1. Send OTP Code
POST /otp/send/
Request: { "phone_number": "+79991234567" }
Success Response (200): { "otp_id": "uuid", "phone_number": "+79991234567", "expires_at": "iso-datetime", "sent": true }
Rate Limit (429): { "error": "Rate limit: max 3 OTPs per 10 minutes" }
Service Down (503): { "error": "OTP service temporarily unavailable" }

### 2. Verify OTP Code
POST /otp/verify/
Request: { "phone_number": "+79991234567", "code": "123456" }
Success (200): { "is_valid": true, "error": null }
Failed (200): { "is_valid": false, "error": "Invalid code. 2 attempts remaining" }
Possible errors: "No active OTP found", "OTP expired", "Max attempts exceeded", "Invalid code. N attempts remaining"

### 3. Resend OTP Code
POST /otp/resend/
Request: { "phone_number": "+79991234567" }
Success (200): same as Send OTP
Cooldown (429): { "error": "Cooldown: wait 42 seconds", "seconds_remaining": 42 }

## UI Flow Requirements

### Screen 1: Phone Input
- Input field for phone number (E.164 format: +XXXXXXXXXXX)
- Phone mask/formatter for the input
- "Send Code" button
- On submit: call POST /otp/send/
- On success: navigate to Screen 2
- On 429: show rate limit error with timer
- On 503: show "Service unavailable" message

### Screen 2: Code Verification
- Show text: "Code sent to WhatsApp +7***4567" (masked phone)
- 6-digit code input (individual boxes preferred)
- "Verify" button
- "Resend code" link/button (disabled for 60 seconds with countdown timer)
- On verify: call POST /otp/verify/
- If is_valid=true: registration/login confirmed, proceed to next screen
- If is_valid=false: show error message from response, keep user on same screen
- On resend: call POST /otp/resend/
- If 429 with seconds_remaining: show countdown timer

### UX Details
- Auto-submit when 6 digits are entered
- Show remaining attempts count from error message
- Countdown timer for resend (start at 60s after send/resend)
- If "Max attempts exceeded" or "OTP expired": show "Send new code" button (calls /otp/send/)
- Phone number validation: must start with +, 8-16 chars total, only digits after +

### Error Handling
- Network errors: "Connection error, try again"
- 503: "Service temporarily unavailable"
- 429 on send: "Too many requests. Try again in N minutes"
- 429 on resend: show countdown timer with seconds_remaining value
- Invalid phone format (400): "Enter valid phone number in format +79991234567"

### State Management
- Store phone_number in component state (needed for verify and resend calls)
- Store countdown timer state
- Store attempts info from error responses

### Design
- Clean, minimal UI
- WhatsApp green accent color (#25D366) for the "Send via WhatsApp" context
- WhatsApp icon near the send button or description text
- Text: "Код будет отправлен в WhatsApp на указанный номер"
```

---

## 5. Чеклист перед продакшеном

- [ ] Сгенерировать `OTP_ADMIN_API_KEY` (надёжный, 32+ символов)
- [ ] Применить миграцию: `python manage.py migrate otp_bot`
- [ ] WAHA Plus лицензия активна
- [ ] Инициализировать бот: `POST /otp-bot/initialize/`
- [ ] Отсканировать QR с WhatsApp номера для OTP
- [ ] Проверить статус: `GET /otp-bot/status/` → `"connected"`
- [ ] Тестовая отправка: `POST /otp/send/` на свой номер
- [ ] Тестовая верификация: `POST /otp/verify/`
- [ ] Добавить Celery Beat задачу для очистки expired кодов
- [ ] Проверить логи на ошибки
- [ ] Убедиться что CORS настроен для домена Lovable app
