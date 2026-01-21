# ZinaPay Integration Documentation

## Обзор

ZinaPay (Ziina) — платежная система из ОАЭ, поддерживающая множество валют и регионов.

**Официальная документация:** https://docs.ziina.com/

**API Base URL:** `https://api-v2.ziina.com/api`

---

## Режимы работы

ZinaPay поддерживает два режима оплаты:

### 1. P2P (Peer-to-Peer) — "Пользователь платит через приложение"
- Пользователь инициирует оплату из мобильного приложения/веб-интерфейса
- Используется для онлайн-покупок, подписок, бронирований
- Фронтенд перенаправляет пользователя на `redirect_url` от ZinaPay
- После оплаты пользователь возвращается на success/failure URL

### 2. POS (Point of Sale) — "Терминал мерчанта с QR-кодом"
- Мерчант генерирует QR-код на своем устройстве
- Покупатель сканирует QR и оплачивает
- Используется для оффлайн-точек, касс, терминалов
- Фронтенд отображает QR-код и ожидает подтверждения оплаты

---

## Поддерживаемые валюты

### Стандартные валюты (2 десятичных знака):
- **AED** — UAE Dirham (по умолчанию)
- **USD** — US Dollar
- **EUR** — Euro
- **GBP** — British Pound
- **SAR** — Saudi Riyal
- **QAR** — Qatari Riyal
- **INR** — Indian Rupee

### Трехзначные валюты (3 десятичных знака):
- **BHD** — Bahraini Dinar
- **KWD** — Kuwaiti Dinar
- **OMR** — Omani Rial

> **Важно:** Для трехзначных валют суммы округляются до ближайших 10 филсов.

> **Валидация валют:** Бэкенд автоматически проверяет, что валюта транзакции входит в список поддерживаемых. Если валюта не поддерживается, API вернет ошибку 400 с детальным описанием поддерживаемых валют. Это защищает от случайных ошибок и попыток использовать неподдерживаемые валюты.

---

## API Endpoints

### 1. Получить конфигурацию ZinaPay для организации

**GET** `/api/v1/organizations/{organization_id}/payment_systems/zinapay/config/`

**Авторизация:** Bearer Token (требуется)

**Права:** Пользователь должен иметь права на просмотр организации

**Пример ответа:**
```json
{
  "currencies": ["AED", "USD", "EUR"],
  "is_active": true,
  "is_confirmed": true
}
```

**Поля:**
- `currencies` — список поддерживаемых валют (пустой массив = все валюты)
- `is_active` — активирован ли ZinaPay для этой организации
- `is_confirmed` — подтвержден ли ZinaPay для этой организации

---

### 2. Обновить список валют

**PATCH** `/api/v1/organizations/{organization_id}/payment_systems/zinapay/config/`

**Авторизация:** Bearer Token (требуется)

**Права:** Пользователь должен иметь права на редактирование организации

**Тело запроса:**
```json
{
  "currencies": ["AED", "USD", "SAR"]
}
```

**Пример ответа:**
```json
{
  "currencies": ["AED", "USD", "SAR"]
}
```

---

### 3. Создать транзакцию (Preprocess)

**POST** `/api/v1/transactions/zinapay/preprocess/`

**Авторизация:** Bearer Token (требуется)

**Описание:**
Создает транзакцию с указанной валютой перед инициализацией платежа. Аналогичен `/api/v1/transactions/preprocess/`, но специфичен для ZinaPay и требует указания валюты.

**Тело запроса:**
```json
{
  "organization": 120,
  "client": 456,
  "cart": null,
  "order_comment": "Optional note",
  "currency": "AED"
}
```

**Поля:**
- `organization` (обязательно, integer) — ID организации
- `client` (опционально, integer) — ID клиента (по умолчанию текущий пользователь)
- `cart` (опционально, integer/null) — ID корзины
- `order_comment` (опционально, string) — комментарий к заказу
- `currency` (обязательно, string) — код валюты (AED, USD, EUR и т.д.)

**Пример ответа:**
```json
{
  "transaction_id": 12345,
  "organization_id": 120,
  "client_id": 456,
  "currency": "AED",
  "status": "waiting_for_payment",
  "payment_status": "in_progress"
}
```

**Валидация:**
- Проверяет, что ZinaPay настроен и активирован для организации
- Проверяет, что валюта поддерживается ZinaPay
- Создает транзакцию с указанной валютой

**Следующий шаг:**
После создания транзакции используйте `transaction_id` для инициализации платежа через endpoint 4.

---

### 4. Инициализировать платеж P2P (онлайн-оплата)

**POST** `/api/v1/transactions/pay/7/`

**Авторизация:** Bearer Token (требуется)

**Тело запроса:**
```json
{
  "transaction_id": 12345
}
```

**Пример ответа:**
```json
{
  "redirect_url": "https://payment.ziina.com/pay/pi_abc123xyz..."
}
```

**Описание:**
- `7` в URL — это ID платежной системы ZinaPay
- Создает Payment Intent в ZinaPay для указанной транзакции
- Возвращает `redirect_url` для перенаправления пользователя
- Автоматически сохраняет `payment_info` в транзакции:
  - `payment_mode`: `"p2p"`
  - `purchase_type`: тип покупки (`"deal"`, `"product"`, `"assistant"`, `"rent"`, `"org_subscription"`, `"user_app"`)
  - `zinapay_payment_intent_id`: ID платежного намерения
  - `success_url`, `failure_url`

**Фронтенд должен:**
1. Получить `redirect_url` из ответа
2. Перенаправить пользователя на эту ссылку: `window.location.href = redirect_url`
3. После оплаты ZinaPay вернет пользователя на `success_url` или `failure_url`

---

### 5. Создать платеж POS (терминал с QR-кодом)

**POST** `/api/v1/transactions/zinapay/pos/create/`

**Авторизация:** Bearer Token (требуется)

**Тело запроса:**
```json
{
  "amount": "100.50",
  "currency": "AED",
  "organization_id": 123,
  "note": "Coffee and pastry",
  "generate_qr": true
}
```

**Поля:**
- `amount` (обязательно, string/number) — сумма платежа
- `currency` (обязательно, string) — код валюты (AED, USD, и т.д.)
- `organization_id` (обязательно, integer) — ID организации
- `note` (опционально, string) — описание платежа
- `generate_qr` (опционально, boolean) — генерировать ли QR-код (по умолчанию `true`)

**Пример ответа:**
```json
{
  "transaction_id": 98765,
  "redirect_url": "https://payment.ziina.com/pay/pi_abc123xyz...",
  "qr_code_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "amount": "100.50",
  "currency": "AED",
  "payment_mode": "pos"
}
```

**Поля ответа:**
- `transaction_id` — ID созданной транзакции
- `redirect_url` — ссылка для оплаты (для вставки в QR)
- `qr_code_base64` — готовый QR-код в формате base64 (data URL)
- `amount` — сумма платежа
- `currency` — валюта
- `payment_mode` — режим работы (`"pos"`)

**Фронтенд должен:**
1. Отобразить QR-код: `<img src="{qr_code_base64}" />`
2. Показать сумму и валюту
3. Начать polling статуса транзакции (см. следующий endpoint)

---

### 6. Проверить статус POS-транзакции (polling)

**GET** `/api/v1/transactions/zinapay/status/?transaction_id={id}`

**Авторизация:** Bearer Token (требуется)

**Query Parameters:**
- `transaction_id` (обязательно) — ID транзакции

**Пример ответа:**
```json
{
  "transaction_id": 98765,
  "is_processed": true,
  "payment_status": "accepted",
  "status": "accepted",
  "amount": "100.50",
  "currency": "AED",
  "payment_mode": "pos"
}
```

**Поля:**
- `transaction_id` — ID транзакции
- `is_processed` — обработана ли транзакция (true = оплата завершена)
- `payment_status` — статус платежа:
  - `"in_progress"` — оплата в процессе
  - `"accepted"` — оплата успешна
  - `"rejected"` — оплата отклонена
- `status` — общий статус транзакции
- `amount` — сумма
- `currency` — валюта
- `payment_mode` — режим (`"pos"` или `"p2p"`)

**Фронтенд должен:**
1. Запускать polling каждые 2-3 секунды
2. Проверять `is_processed === true`
3. Если `true` и `payment_status === "accepted"` → показать успех
4. Если `payment_status === "rejected"` → показать ошибку
5. Прекратить polling после завершения

**Пример polling (JavaScript):**
```javascript
async function pollPaymentStatus(transactionId) {
  const maxAttempts = 60; // 60 попыток = 3 минуты
  let attempts = 0;

  const interval = setInterval(async () => {
    try {
      const response = await fetch(
        `/api/v1/transactions/zinapay/status/?transaction_id=${transactionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (data.is_processed) {
        clearInterval(interval);

        if (data.payment_status === 'accepted') {
          showSuccess();
        } else {
          showError();
        }
      }

      attempts++;
      if (attempts >= maxAttempts) {
        clearInterval(interval);
        showTimeout();
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, 3000); // 3 секунды
}
```

---

### 7. Webhook (для бэкенда, но полезно знать)

**POST** `/api/v1/transactions/zinapay/webhook/`

**Авторизация:** Не требуется (проверка через IP whitelist + HMAC)

**Описание:**
- ZinaPay отправляет уведомления на этот endpoint при изменении статуса платежа
- Бэкенд автоматически обрабатывает webhook и обновляет статус транзакции
- Фронтенд НЕ должен вызывать этот endpoint напрямую

**GET Redirect** `/api/v1/transactions/zinapay/callback/`

**Query Parameters:**
- `tx={transaction_id}` — ID транзакции
- `payment_intent_id` (опционально) — ID платежного намерения

**Описание:**
- Используется как success/failure URL для перенаправления пользователя
- Проверяет статус платежа и перенаправляет на финальный success/failure URL
- Фронтенд получит финальное перенаправление из `payment_info`

---

## Статусы платежа (ZinaPay)

ZinaPay использует следующие статусы Payment Intent:

| Статус | Описание |
|--------|----------|
| `requires_payment_instrument` | Ожидает выбора способа оплаты |
| `pending` | Платеж в обработке |
| `requires_user_action` | Требуется действие пользователя |
| `completed` | Платеж завершен успешно ✅ |
| `failed` | Платеж провален ❌ |
| `canceled` | Платеж отменен пользователем |

---

## Статусы транзакции (Backend)

| payment_status | Описание |
|----------------|----------|
| `in_progress` | Оплата в процессе (начальный статус) |
| `accepted` | Оплата принята и обработана |
| `rejected` | Оплата отклонена |

| is_processed | Описание |
|--------------|----------|
| `false` | Транзакция еще не обработана |
| `true` | Транзакция обработана (списание/начисление выполнено) |

---

## Типы покупок (purchase_type)

При создании платежа бэкенд автоматически определяет тип покупки:

| purchase_type | Описание |
|---------------|----------|
| `deal` | Обычная сделка/покупка |
| `product` | Покупка товара из каталога |
| `assistant` | Оплата услуг ассистента |
| `rent` | Бронирование/аренда |
| `org_subscription` | Подписка организации |
| `user_app` | Покупка в приложении |
| `pos_payment` | Платеж через POS-терминал |

---

## Конвертация сумм (филсы)

ZinaPay работает с **филсами** (базовые единицы):

### Стандартные валюты (2 знака):
- 1.00 AED = 100 fils
- 100.50 AED = 10050 fils

### Трехзначные валюты (3 знака):
- 1.000 BHD = 1000 fils
- 100.500 KWD = 100500 fils (округляется до 100500)

Бэкенд автоматически конвертирует суммы. Фронтенд работает с обычными десятичными числами.

---

## Flow диаграммы

### P2P Payment Flow (онлайн-оплата)

```
Пользователь                  Фронтенд                Backend              ZinaPay
     |                            |                       |                    |
     |-- Выбирает товары -------->|                       |                    |
     |                            |-- POST /zinapay/preprocess/ --------------->|
     |                            |   {organization, currency: "AED"}          |
     |                            |<-- {transaction_id: 12345} ----------------|
     |                            |                       |                    |
     |-- Вводит сумму, скидки --->|                       |                    |
     |-- Нажимает "Оплатить" ---->|                       |                    |
     |                            |-- POST /transactions/pay/7/ --------------->|
     |                            |   {transaction_id: 12345}                  |
     |                            |                       |-- create_payment_intent() ->
     |                            |                       |<-- {redirect_url} -|
     |                            |<-- {redirect_url} ----|                    |
     |                            |                       |                    |
     |<-- window.location = redirect_url ----------------|                    |
     |                            |                       |                    |
     |-------------------------------- Перенаправление на ZinaPay ------------->|
     |<----------------------- Страница оплаты ZinaPay ----------------------->|
     |-- Вводит данные карты ---->|                       |                    |
     |                            |                       |                    |
     |                            |                       |<-- Webhook: status=completed
     |                            |                       |-- Обработка транзакции
     |<---- Редирект на success_url ----------------------|                    |
     |                            |                       |                    |
     |-- Страница успеха -------->|                       |                    |
```

### POS Payment Flow (терминал)

```
Мерчант                     Фронтенд                Backend              ZinaPay         Покупатель
   |                            |                       |                    |                |
   |-- Вводит сумму ----------->|                       |                    |                |
   |                            |-- POST /pos/create/ ->|                    |                |
   |                            |                       |-- create_payment_intent() ->        |
   |                            |                       |<-- {redirect_url} -|                |
   |                            |<-- {qr_code_base64} --|                    |                |
   |                            |                       |                    |                |
   |<-- Показывает QR-код ------|                       |                    |                |
   |                            |-- Polling /status/ -->|                    |                |
   |                            |<-- {is_processed: false}                   |                |
   |                            |                       |                    |                |
   |                            |                       |                    |<-- Сканирует QR
   |                            |                       |                    |<-- Оплачивает -|
   |                            |                       |<-- Webhook: completed              |
   |                            |                       |-- Обработка транзакции             |
   |                            |-- Polling /status/ -->|                    |                |
   |                            |<-- {is_processed: true, payment_status: "accepted"}        |
   |<-- Показывает успех -------|                       |                    |                |
```

---

## Обработка ошибок

### Коды ошибок HTTP

| Код | Описание |
|-----|----------|
| 400 | Неверные параметры запроса |
| 404 | Транзакция/организация не найдена |
| 502 | ZinaPay API недоступен или вернул ошибку |

### Примеры ошибок

**ZinaPay не настроен:**
```json
{
  "error": "ZinaPay is not configured for this organization"
}
```

**ZinaPay не активирован:**
```json
{
  "error": "ZinaPay is not activated for this organization"
}
```

**Неподдерживаемая валюта (POS):**
```json
{
  "currency": [
    "Unsupported currency for ZinaPay: XYZ. Supported currencies: AED, BHD, EUR, GBP, INR, KWD, OMR, QAR, SAR, USD"
  ]
}
```

**Неподдерживаемая валюта (P2P):**
```json
{
  "error": "Unsupported currency for ZinaPay: XYZ. Supported currencies: AED, BHD, EUR, GBP, INR, KWD, OMR, QAR, SAR, USD"
}
```

**Ошибка создания платежа:**
```json
{
  "error": "Failed to create ZinaPay payment. Please try again."
}
```

---

## Проверка доступности ZinaPay

Перед отображением кнопки "Оплатить через ZinaPay" фронтенд должен проверить:

1. **GET** `/api/v1/organizations/{id}/payment_systems/zinapay/config/`
2. Проверить: `is_active === true && is_confirmed === true`
3. Проверить: валюта транзакции входит в `currencies` (или массив пустой)

**Пример кода:**
```javascript
async function isZinaPayAvailable(organizationId, currency) {
  try {
    const response = await fetch(
      `/api/v1/organizations/${organizationId}/payment_systems/zinapay/config/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    if (!response.ok) {
      return false; // ZinaPay не настроен
    }

    const data = await response.json();

    // Проверка активности
    if (!data.is_active || !data.is_confirmed) {
      return false;
    }

    // Проверка валюты (пустой массив = все валюты)
    if (data.currencies.length === 0) {
      return true;
    }

    return data.currencies.includes(currency);

  } catch (error) {
    console.error('Error checking ZinaPay availability:', error);
    return false;
  }
}
```

---

## Примеры UI компонентов

### Кнопка оплаты P2P

```jsx
import React, { useState } from 'react';

function ZinaPayButton({ organizationId, cartId, currency }) {
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    setLoading(true);

    try {
      // Шаг 1: Создать транзакцию с валютой (preprocess)
      const preprocessResponse = await fetch(
        '/api/v1/transactions/zinapay/preprocess/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            organization: organizationId,
            cart: cartId,
            currency: currency  // AED, USD, EUR, etc.
          })
        }
      );

      if (!preprocessResponse.ok) {
        throw new Error('Transaction creation failed');
      }

      const { transaction_id } = await preprocessResponse.json();

      // Шаг 2: Инициализировать платеж через /pay/7/
      const paymentResponse = await fetch(
        '/api/v1/transactions/pay/7/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            transaction_id: transaction_id
          })
        }
      );

      if (!paymentResponse.ok) {
        throw new Error('Payment initialization failed');
      }

      const data = await paymentResponse.json();

      // Шаг 3: Перенаправление на ZinaPay
      window.location.href = data.redirect_url;

    } catch (error) {
      console.error('Payment error:', error);
      alert('Failed to initiate payment. Please try again.');
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handlePayment}
      disabled={loading}
      className="zinapay-button"
    >
      {loading ? 'Processing...' : 'Pay with ZinaPay'}
    </button>
  );
}
```

### POS терминал с QR-кодом

```jsx
import React, { useState, useEffect } from 'react';

function POSTerminal({ organizationId, onSuccess, onError }) {
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('AED');
  const [note, setNote] = useState('');
  const [qrCode, setQrCode] = useState(null);
  const [transactionId, setTransactionId] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (transactionId) {
      const interval = setInterval(checkPaymentStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [transactionId]);

  const createPayment = async () => {
    setLoading(true);

    try {
      const response = await fetch(
        '/api/v1/transactions/zinapay/pos/create/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            amount,
            currency,
            organization_id: organizationId,
            note,
            generate_qr: true
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to create payment');
      }

      const data = await response.json();

      setQrCode(data.qr_code_base64);
      setTransactionId(data.transaction_id);

    } catch (error) {
      console.error('Error:', error);
      onError(error);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async () => {
    try {
      const response = await fetch(
        `/api/v1/transactions/zinapay/status/?transaction_id=${transactionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (data.is_processed) {
        if (data.payment_status === 'accepted') {
          onSuccess(data);
        } else {
          onError(new Error('Payment rejected'));
        }
        setTransactionId(null); // Остановить polling
      }

    } catch (error) {
      console.error('Polling error:', error);
    }
  };

  if (qrCode) {
    return (
      <div className="qr-display">
        <h2>Scan to Pay</h2>
        <img src={qrCode} alt="Payment QR Code" />
        <p>Amount: {amount} {currency}</p>
        <p>Waiting for payment...</p>
        <button onClick={() => {
          setQrCode(null);
          setTransactionId(null);
        }}>
          Cancel
        </button>
      </div>
    );
  }

  return (
    <div className="pos-form">
      <h2>POS Terminal</h2>
      <input
        type="number"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="Amount"
      />
      <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
        <option value="AED">AED</option>
        <option value="USD">USD</option>
        <option value="EUR">EUR</option>
        <option value="SAR">SAR</option>
      </select>
      <input
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Note (optional)"
      />
      <button
        onClick={createPayment}
        disabled={loading || !amount}
      >
        {loading ? 'Creating...' : 'Generate QR Code'}
      </button>
    </div>
  );
}
```

---

## Безопасность

### IP Whitelist
ZinaPay отправляет webhook только с официальных IP:
- `3.29.184.186`
- `3.29.190.95`
- `20.233.47.127`

Бэкенд автоматически проверяет IP отправителя.

### HMAC подпись
Если настроен `webhook_secret`, бэкенд проверяет HMAC SHA-256 подпись в заголовке `X-Hmac-Signature`.

### Двойная верификация
При получении webhook со статусом `completed`, бэкенд дополнительно делает GET запрос к ZinaPay API для проверки реального статуса.

---

## Тестирование

### Тестовый режим
При создании Payment Intent можно передать параметр `test: true` для создания тестового платежа (не списывается реальная сумма).

Это делается на уровне бэкенд-сервиса и не доступно напрямую из API endpoints для фронтенда.

---

## Логирование

Все операции ZinaPay логируются с префиксом `[ZinaPay]`:
- `[ZinaPay] Creating payment intent`
- `[ZinaPay] Payment intent created successfully`
- `[ZinaPay] Webhook received`
- `[ZinaPay POS] Transaction created`
- `[ZinaPay P2P] Payment intent created from NewInitPaymentView`

При возникновении проблем попросите бэкенд-разработчика проверить логи.

---

## Частые вопросы (FAQ)

### Q: Как узнать, что платеж завершен в режиме P2P?
**A:** После оплаты пользователь будет перенаправлен на `success_url` (если успешно) или `failure_url` (если ошибка). Проверьте параметры URL или состояние транзакции через API.

### Q: Как долго действителен Payment Intent?
**A:** По умолчанию 24 часа. Можно настроить через параметр `expiry` (Unix timestamp в миллисекундах).

### Q: Можно ли отменить платеж?
**A:** Пользователь может отменить платеж на странице ZinaPay. Webhook придет со статусом `canceled`.

### Q: Поддерживаются ли recurring платежи?
**A:** Нет, ZinaPay integration поддерживает только разовые платежи.

### Q: Как работает поле `allow_tips`?
**A:** Если `true`, на странице оплаты ZinaPay будет возможность добавить чаевые. Сумма чаевых придет в `tip_amount` в webhook.

### Q: Нужно ли фронтенду обрабатывать webhook?
**A:** Нет, webhook обрабатывается бэкендом автоматически. Фронтенд только делает polling статуса (для POS) или получает редирект (для P2P).

---

## Контакты поддержки

**ZinaPay Support:**
- Документация: https://docs.ziina.com/
- Email: support@ziina.com

**Backend Developer:**
- Проверить логи для отладки
- Настроить webhook_secret для безопасности
- Добавить/удалить валюты через PATCH endpoint

---

## Changelog

### Version 1.0 (2025-01-09)
- ✅ P2P payment flow (онлайн-оплата)
- ✅ POS terminal flow (QR-код терминал)
- ✅ Webhook обработка (IP whitelist + HMAC)
- ✅ Поддержка 10 валют (7 стандартных + 3 трехзначные)
- ✅ Автоматическая обработка типов покупок (deal, product, assistant, rent, org_subscription, user_app)
- ✅ Генерация QR-кодов для POS
- ✅ Конфигурация валют на уровне организации

---

## Итого: Quick Start для фронтенда

### P2P (обычная оплата):
1. Проверить доступность: `GET /organizations/{id}/payment_systems/zinapay/config/`
2. **Создать транзакцию**: `POST /transactions/zinapay/preprocess/` с `{organization, currency, cart}`
3. Получить `transaction_id` из ответа
4. **Инициализировать платеж**: `POST /transactions/pay/7/` с `{transaction_id}`
5. Перенаправить пользователя: `window.location.href = response.redirect_url`
6. Дождаться возврата на `success_url` или `failure_url`

### POS (терминал):
1. Создать платеж: `POST /transactions/zinapay/pos/create/`
2. Показать QR-код: `<img src="{qr_code_base64}" />`
3. Polling статуса: `GET /transactions/zinapay/status/?transaction_id={id}` каждые 3 секунды
4. При `is_processed: true` → показать результат

---

**Документация создана:** 2025-01-09
