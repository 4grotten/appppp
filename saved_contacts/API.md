# Saved Contacts API

**Base URL:** `/api/v1/contacts/`
**Auth:** `Authorization: Token <token>`

---

## Endpoints

### 1. Список контактов

```
GET /api/v1/contacts/
```

**Query params:** `?page=1&limit=20`

**Response:**
```json
{
  "total_count": 2,
  "total_pages": 1,
  "list": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "John Doe",
      "phone": "+971501234567",
      "email": "john@example.com",
      "company": "Acme Inc",
      "position": "CEO",
      "avatar": null,
      "avatar_url": null,
      "notes": "Important client",
      "payment_methods": [],
      "social_links": [],
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z"
    }
  ]
}
```

---

### 2. Создать контакт

```
POST /api/v1/contacts/
Content-Type: application/json
```

**Request:**
```json
{
  "full_name": "John Doe",
  "phone": "+971501234567",
  "email": "john@example.com",
  "company": "Acme Inc",
  "position": "CEO",
  "notes": "VIP client",
  "payment_methods": [
    {"id": "pm1", "type": "card", "label": "Visa", "value": "4111...1111"},
    {"id": "pm2", "type": "iban", "label": "Bank", "value": "AE123456"}
  ],
  "social_links": [
    {"id": "sl1", "networkId": "linkedin", "networkName": "LinkedIn", "url": "https://linkedin.com/in/john"}
  ]
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| full_name | string | да | Имя контакта |
| phone | string | нет | Телефон |
| email | string | нет | Email |
| company | string | нет | Компания |
| position | string | нет | Должность |
| notes | string | нет | Заметки |
| payment_methods | array | нет | Платёжные методы |
| social_links | array | нет | Соц. сети |

**Response:** `201 Created` — созданный контакт

---

### 3. Получить контакт

```
GET /api/v1/contacts/{id}/
```

**Response:** `200 OK` — объект контакта

---

### 4. Обновить контакт

```
PATCH /api/v1/contacts/{id}/
Content-Type: application/json
```

**Request:** только изменяемые поля
```json
{
  "company": "New Company",
  "position": "CTO"
}
```

**Response:** `200 OK` — обновлённый контакт

---

### 5. Удалить контакт

```
DELETE /api/v1/contacts/{id}/
```

**Response:** `204 No Content`

---

### 6. Загрузить аватар

```
POST /api/v1/contacts/{id}/avatar/
Content-Type: multipart/form-data
```

**Request:**
```
file: <image file>
```

**Response:** `200 OK` — контакт с заполненным `avatar_url`

---

### 7. Удалить аватар

```
DELETE /api/v1/contacts/{id}/avatar/
```

**Response:** `200 OK` — контакт с `avatar_url: null`

---

## Структуры данных

### PaymentMethod

```json
{
  "id": "string",
  "type": "card | iban | crypto | paypal | applepay | googlepay | wallet | other",
  "label": "string",
  "value": "string",
  "network": "string (optional, для crypto)"
}
```

### ContactSocialLink

```json
{
  "id": "string",
  "networkId": "string",
  "networkName": "string",
  "url": "string"
}
```

---

## TypeScript Types

```typescript
interface SavedContact {
  id: string;
  full_name: string;
  phone?: string;
  email?: string;
  company?: string;
  position?: string;
  avatar_url?: string;
  notes?: string;
  payment_methods: PaymentMethod[];
  social_links: ContactSocialLink[];
  created_at: string;
  updated_at: string;
}

interface PaymentMethod {
  id: string;
  type: 'card' | 'iban' | 'crypto' | 'paypal' | 'applepay' | 'googlepay' | 'wallet' | 'other';
  label: string;
  value: string;
  network?: string;
}

interface ContactSocialLink {
  id: string;
  networkId: string;
  networkName: string;
  url: string;
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Невалидные данные |
| 401 | Не авторизован |
| 404 | Контакт не найден |

---

## Примеры cURL

```bash
# Список контактов
curl -H "Authorization: Token <token>" \
  https://api.example.com/api/v1/contacts/

# Создать контакт
curl -X POST \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Doe", "phone": "+971501234567"}' \
  https://api.example.com/api/v1/contacts/

# Загрузить аватар
curl -X POST \
  -H "Authorization: Token <token>" \
  -F "file=@avatar.jpg" \
  https://api.example.com/api/v1/contacts/{id}/avatar/
```
