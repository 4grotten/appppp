# WAHA WhatsApp Bot Binding Endpoints

Этот документ описывает API, который используем для привязки WhatsApp бота через WAHA и получения QR.

## 1) Аутентификация

### Backend API (Django)
- База: `/api/v1/messenger-bots/`
- Заголовок:

```http
Authorization: Token <APP_TOKEN>
Content-Type: application/json
```

### WAHA API (напрямую, для диагностики)
- Из хоста сервера: `http://localhost:3005`
- Из других контейнеров: `http://waha:3000`
- Из контейнера WAHA: `http://localhost:3000`
- Заголовок:

```http
X-Api-Key: <WAHA_API_KEY>
```

---

## 2) Основной флоу привязки WhatsApp через Backend API

### 2.1 Создать WAHA-бота для организации
**POST** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/`

Body:

```json
{
  "is_active": true
}
```

Что делает:
- создаёт `WhatsAppBot` с `provider=WAHA`
- пробует стартовать WAHA-сессию

---

### 2.2 Запустить/перезапустить сессию вручную
**POST** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/session/`

Body: пустой

Ответ (пример):

```json
{
  "message": "Session started",
  "status": "pending"
}
```

---

### 2.3 Проверить статус сессии
**GET** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/session/`

Ответ (пример):

```json
{
  "session_name": "org_120",
  "status": "scan_qr",
  "status_display": "Ожидает сканирования QR",
  "qr_code": "...",
  "connected_phone": null,
  "is_healthy": true,
  "waha_status": {
    "status": "SCAN_QR_CODE",
    "name": "org_120",
    "me": null
  }
}
```

---

### 2.4 Получить QR для сканирования
**GET** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/qr/`

Ответ (пример):

```json
{
  "qr_code": "2@....",
  "message": "Scan this QR code with WhatsApp",
  "session_status": "scan_qr",`
  "waha_status": {
    "status": "SCAN_QR_CODE",
    "name": "org_120",
    "me": null
  },
  "last_error": null
}
```

Важно:
- `qr_code` здесь часто в **raw формате** (не PNG).
- raw-строку нужно преобразовать в QR (или получить PNG напрямую из WAHA, см. раздел 4).

---

## 3) Сервисные endpoint’ы (управление сессией)

### 3.1 Logout сессии (потребуется новый QR)
**POST** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/session/logout/`

### 3.2 Полное удаление сессии WAHA
**POST** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/session/delete/`

### 3.3 Rebind номера (смена телефона)
**POST** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/session/rebind/`

Что делает:
- сохраняет предыдущий номер
- logout + delete старой сессии
- стартует новую
- возвращает новый `qr_code`

### 3.4 Получить/обновить конфиг бота
- **GET** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/`
- **PATCH** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/`

PATCH поддерживает:

```json
{
  "is_active": true,
  "is_ai_enabled": true
}
```

### 3.5 Удалить конфиг бота
**DELETE** `/api/v1/messenger-bots/whatsapp/waha/{organization_id}/`

---

## 4) Прямые WAHA endpoint’ы (для диагностики)

Ниже маршруты WAHA, которые полезны, когда нужно быстро проверить, где проблема (backend или WAHA).

### 4.1 Проверка списка сессий
**GET** `/api/sessions`

```bash
curl -s -H "X-Api-Key: <WAHA_API_KEY>" "http://localhost:3005/api/sessions"
```

### 4.2 Проверка конкретной сессии
**GET** `/api/sessions/{session}`

```bash
curl -s -H "X-Api-Key: <WAHA_API_KEY>" "http://localhost:3005/api/sessions/org_120"
```

### 4.3 Старт (upsert) сессии
**POST** `/api/sessions/start`

```bash
curl -i -X POST \
  -H "X-Api-Key: <WAHA_API_KEY>" \
  -H "Content-Type: application/json" \
  "http://localhost:3005/api/sessions/start" \
  -d '{"name":"org_120"}'
```

### 4.4 Получить QR в raw
**GET** `/api/{session}/auth/qr?format=raw`

```bash
curl -s -H "X-Api-Key: <WAHA_API_KEY>" "http://localhost:3005/api/org_120/auth/qr?format=raw"
```

### 4.5 Получить QR как PNG
**GET** `/api/{session}/auth/qr`

```bash
curl -H "X-Api-Key: <WAHA_API_KEY>" "http://localhost:3005/api/org_120/auth/qr" --output qr.png
file qr.png
```

### 4.6 Logout сессии
**POST** `/api/sessions/logout`

```bash
curl -i -X POST \
  -H "X-Api-Key: <WAHA_API_KEY>" \
  -H "Content-Type: application/json" \
  "http://localhost:3005/api/sessions/logout" \
  -d '{"name":"org_120"}'
```

### 4.7 Удаление сессии
**DELETE** `/api/sessions/{session}`

```bash
curl -i -X DELETE -H "X-Api-Key: <WAHA_API_KEY>" "http://localhost:3005/api/sessions/org_120"
```

---

## 5) Статусы и интерпретация

Типовые WAHA статусы:
- `WORKING` — подключено, бот онлайн
- `SCAN_QR_CODE` — ждёт сканирования QR
- `FAILED` — сессия сломана, QR не выдастся (обычно будет `422`)
- `STARTING` — запускается

Если приходит:

```json
{
  "error": "Session status is not as expected...",
  "status": "FAILED",
  "expected": ["SCAN_QR_CODE"]
}
```

Действия:
1. `DELETE /api/sessions/{session}`
2. `POST /api/sessions/start`
3. дождаться `SCAN_QR_CODE`
4. снова получить QR

---

## 6) Готовый минимальный сценарий (backend only)

```bash
# 1) Создать WAHA-бота
curl -X POST \
  -H "Authorization: Token <APP_TOKEN>" \
  -H "Content-Type: application/json" \
  "https://<your-domain>/api/v1/messenger-bots/whatsapp/waha/120/" \
  -d '{"is_active": true}'

# 2) Запустить сессию
curl -X POST \
  -H "Authorization: Token <APP_TOKEN>" \
  "https://<your-domain>/api/v1/messenger-bots/whatsapp/waha/120/session/"

# 3) Получить QR
curl -H "Authorization: Token <APP_TOKEN>" \
  "https://<your-domain>/api/v1/messenger-bots/whatsapp/waha/120/qr/"
```

После сканирования проверь статус:

```bash
curl -H "Authorization: Token <APP_TOKEN>" \
  "https://<your-domain>/api/v1/messenger-bots/whatsapp/waha/120/session/"
```

Ожидаемый результат: WAHA `WORKING`, а в боте заполнится `connected_phone_number`.
