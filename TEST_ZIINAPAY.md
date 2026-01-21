# ZinaPay - Пошаговое тестирование с реальными деньгами

## Базовый URL
```
https://test.apofiz.com
```

---

## Шаг 1: Авторизация

**POST** `https://test.apofiz.com/api/v1/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
    "phone_number": "+971XXXXXXXXX",
    "password": "your_password"
}
```

**Ответ:**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "..."
}
```

Сохрани `access` - это твой токен для всех запросов.

---

## Шаг 2: Preprocess (создание транзакции)

**POST** `https://test.apofiz.com/api/v1/transactions/preprocess/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Body (минимальный):**
```json
{
    "organization": 1,
    "currency": "AED"
}
```

**Body (с корзиной товаров):**
```json
{
    "organization": 1,
    "currency": "AED",
    "cart": [
        {
            "product": 123,
            "quantity": 1
        }
    ],
    "order_comment": "Test order"
}
```

**Ответ:**
```json
{
    "transaction_id": 8212,
    "organization_id": 1,
    "client_id": 100,
    "currency": "AED",
    "status": "accepted",
    "payment_status": "IN_PROGRESS"
}
```

**Запомни `transaction_id`!**

---

## Шаг 3: Инициализация платежа ZinaPay

**POST** `https://test.apofiz.com/api/v1/transactions/pay/7/`

> `7` = ID платежной системы ZinaPay

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Body:**
```json
{
    "transaction_id": 8212
}
```

**Успешный ответ:**
```json
{
    "redirect_url": "https://pay.ziina.com/c/pi_abc123def456..."
}
```

**Возможные ошибки:**
| Ошибка | Причина |
|--------|---------|
| `ZinaPay is not configured for this organization` | У организации не настроен ZinaPay |
| `Transaction not found` | Неверный transaction_id |
| `This transaction is already paid` | Транзакция уже оплачена |
| `Unsupported currency for ZinaPay` | Валюта не поддерживается (используй AED, USD, EUR) |

---

## Шаг 4: Оплата

1. Скопируй `redirect_url` из ответа
2. Открой в браузере
3. Введи данные карты
4. Подтверди оплату

**Тестовые карты ZinaPay:**
| Карта | Результат |
|-------|-----------|
| `4242 4242 4242 4242` | Успешная оплата |
| `4000 0000 0000 0002` | Отклонена |

Любой CVV, любая будущая дата.

---

## Шаг 5: Проверка статуса

После оплаты ZinaPay автоматически отправит webhook на сервер.

**GET** `https://test.apofiz.com/api/v1/statistics/transactions/8212/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Ответ (успешная оплата):**
```json
{
    "id": 8212,
    "is_processed": true,
    "payment_status": "ACCEPTED",
    "status": "accepted"
}
```

---

## Поддерживаемые валюты

ZinaPay поддерживает:
- `AED` - Дирхам ОАЭ
- `USD` - Доллар США
- `EUR` - Евро
- `GBP` - Фунт стерлингов
- `SAR` - Саудовский риял
- `QAR` - Катарский риял
- `INR` - Индийская рупия
- `BHD` - Бахрейнский динар (3 знака после запятой)
- `KWD` - Кувейтский динар (3 знака после запятой)
- `OMR` - Оманский риал (3 знака после запятой)

---

## Мониторинг на сервере

SSH на сервер и смотри логи:

```bash
# Все логи
tail -f /var/log/apofiz/gunicorn.log

# Только ZinaPay
tail -f /var/log/apofiz/gunicorn.log | grep -i zinapay
```

Debug-вывод:
```
============================================================
[ZinaPay DEBUG] === INIT PAYMENT START ===
[ZinaPay DEBUG] transaction_id=8212
[ZinaPay DEBUG] config found: True
[ZinaPay DEBUG] amount_fils=10000 (original: 100.00)
[ZinaPay DEBUG] ZinaPay API response:
[ZinaPay DEBUG]   payment_intent_id=pi_xxx
[ZinaPay DEBUG]   redirect_url=https://pay.ziina.com/...
[ZinaPay DEBUG] === INIT PAYMENT SUCCESS ===
============================================================
```

---

## Webhook (автоматическая обработка)

ZinaPay отправляет POST на:
```
https://test.apofiz.com/api/v1/transactions/zinapay/result/
```

IP адреса ZinaPay (whitelist):
- `3.29.184.186`
- `3.29.190.95`
- `20.233.47.127`

Логи webhook:
```
============================================================
[ZinaPay DEBUG] === WEBHOOK POST RECEIVED ===
[ZinaPay DEBUG] client_ip: 3.29.184.186
[ZinaPay DEBUG] IP check: OK
[ZinaPay DEBUG] status: completed
[ZinaPay DEBUG] Payment processed successfully!
============================================================
```

---

## Быстрый чеклист

1. [ ] Авторизоваться, получить access token
2. [ ] POST `/transactions/preprocess/` → получить `transaction_id`
3. [ ] POST `/transactions/pay/7/` → получить `redirect_url`
4. [ ] Открыть `redirect_url` в браузере
5. [ ] Оплатить картой
6. [ ] Проверить статус транзакции (is_processed = true)

---

## Проверка конфигурации организации

Django shell:
```python
from organizations.models import ZinaPayOrganizationPaymentSystem, Organization

org = Organization.objects.get(id=1)
print(f"zina_pay_activated: {org.zina_pay_activated}")
print(f"zina_pay_confirmed: {org.zina_pay_confirmed}")

config = ZinaPayOrganizationPaymentSystem.objects.filter(organization=org).first()
if config:
    print(f"api_token: {config.api_token[:20]}...")
    print(f"currencies: {list(config.currencies.values_list('code', flat=True))}")
else:
    print("ZinaPay NOT configured!")
```

---

## Если что-то не работает

| Симптом | Проверка |
|---------|----------|
| `502 Bad Gateway` | Проверь логи сервера, ZinaPay API может быть недоступен |
| Транзакция не обновляется | Проверь что webhook дошел (смотри логи) |
| `IP not whitelisted` | Webhook пришел не с IP ZinaPay (нормально для тестов вручную) |
| `create_payment_intent returned None` | Проверь api_token организации в ZinaPayOrganizationPaymentSystem |
