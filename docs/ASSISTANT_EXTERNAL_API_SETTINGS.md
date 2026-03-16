# Assistant External API Settings

## Назначение

Endpoint используется для чтения и обновления настроек внешнего API, которые затем попадают в training data ассистента и используются в промпте/обучении.

## Endpoint

- Method: GET
- Method: PATCH
- Path: /assistant/<pk>/external-api/
- View: AssistantExternalApiSettingsView

Где `<pk>` — это ID ассистента.

## Авторизация и доступ

- Требуется авторизация: `IsAuthenticated`.
- Доступ на изменение/чтение есть только у пользователя, у которого есть право редактировать организацию ассистента.
- При отсутствии прав возвращается `403` с сообщением `No rights to edit organization`.

## Поля

Endpoint работает со следующими полями:

- `external_api_key` (string, optional)
- `external_api_path` (string, optional, URL)
- `external_api_name` (string, optional)
- `external_api_description` (string, optional)
- `external_api_body` (object, optional)
- `external_api_methods` (array[string], optional)

### Валидация external_api_methods

Разрешенные HTTP методы:

- GET
- POST
- PUT
- PATCH
- DELETE
- OPTIONS
- HEAD

Дополнительно:

- методы нормализуются в uppercase;
- дубликаты удаляются;
- можно передать строку через запятую (например `"get, post"`), она будет преобразована в массив.

## Примеры

### GET

Request:

```http
GET /assistant/42/external-api/
Authorization: Bearer <token>
```

Response 200:

```json
{
  "external_api_key": "secret-key",
  "external_api_path": "https://api.example.com/orders",
  "external_api_name": "Orders API",
  "external_api_description": "Получение и синхронизация заказов",
  "external_api_body": {
    "client_id": "{{user_id}}",
    "include_history": true
  },
  "external_api_methods": ["GET", "POST"]
}
```

### PATCH

Request:

```http
PATCH /assistant/42/external-api/
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "external_api_name": "Orders API",
  "external_api_path": "https://api.example.com/orders",
  "external_api_description": "API для получения заказов клиента",
  "external_api_body": {
    "customer_id": "{{user_id}}",
    "locale": "ru"
  },
  "external_api_methods": ["post", "get"]
}
```

Response 200:

```json
{
  "external_api_key": "secret-key",
  "external_api_path": "https://api.example.com/orders",
  "external_api_name": "Orders API",
  "external_api_description": "API для получения заказов клиента",
  "external_api_body": {
    "customer_id": "{{user_id}}",
    "locale": "ru"
  },
  "external_api_methods": ["POST", "GET"]
}
```

## Как это попадает в обучение ассистента

При формировании training data эти поля вкладываются в:

- `training_data.assistant_info.external_api.name`
- `training_data.assistant_info.external_api.path`
- `training_data.assistant_info.external_api.api_key`
- `training_data.assistant_info.external_api.description`
- `training_data.assistant_info.external_api.body`
- `training_data.assistant_info.external_api.methods`

То есть фронт может передавать эти настройки через PATCH endpoint, и они попадают в контекст, который используется ассистентом для ответа.
