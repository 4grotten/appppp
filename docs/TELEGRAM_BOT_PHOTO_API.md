# API для смены фото Telegram бота

## Endpoint

```
POST /api/v1/messenger-bots/telegram/{organization_id}/settings/
```

---

## Как работает

```
Frontend                    Backend                         Telegram
   │                           │                                │
   │  POST /settings/          │                                │
   │  photo: File              │                                │
   ├──────────────────────────►│                                │
   │                           │  Celery task                   │
   │                           ├───────────────────────────────►│
   │                           │  Telethon userbot connects     │
   │                           │  /setuserpic → @BotFather      │
   │                           │  @bot_username                 │
   │                           │  [photo file]                  │
   │                           │◄───────────────────────────────┤
   │  {"photo": {"success":    │  BotFather: "Success"          │
   │    true}}                 │                                │
   │◄──────────────────────────┤                                │
```

> **Почему так сложно?** Telegram Bot API **НЕ имеет** метода `setMyPhoto`.
> Фото бота можно изменить только через @BotFather.
> Бэкенд использует userbot (Telethon) для автоматизации этого процесса.

---

## Варианты отправки фото

### 1. Прямая загрузка файла (рекомендуется)

```javascript
const formData = new FormData();

// Можно отправить вместе с name/description или отдельно
formData.append('name', 'Название бота');           // опционально
formData.append('description', 'Описание бота');   // опционально
formData.append('photo', fileInput.files[0]);      // File объект

const response = await fetch('/api/v1/messenger-bots/telegram/101/settings/', {
    method: 'POST',
    headers: {
        'Authorization': 'Token YOUR_TOKEN'
        // НЕ указывать Content-Type — браузер добавит сам с boundary
    },
    body: formData
});

const result = await response.json();
// { "name": {"success": true}, "photo": {"success": true} }
```

### 2. После кроппера (текущий код TelegramAiSettings)

```javascript
// В handleSubmit:
const formData = new FormData();

if (values.nickname !== initial.nickname) {
    formData.append("name", values.nickname);
}

if (values.description !== initial.description) {
    formData.append("description", values.description);
}

// croppedAvatar — это File объект из кроппера (images[0].original)
if (values.croppedAvatar && values.croppedAvatar instanceof File) {
    formData.append("photo", values.croppedAvatar);
}

await axios.post(`/messenger-bots/telegram/${orgID}/settings/`, formData);
```

### 3. Через URL (альтернатива)

```javascript
// Если уже загрузили фото через /api/v1/files/
const formData = new FormData();
formData.append('photo_url', 'https://apofiz-media.s3.../image.jpg');

await fetch('/api/v1/messenger-bots/telegram/101/settings/', {
    method: 'POST',
    headers: { 'Authorization': 'Token ...' },
    body: formData
});
```

---

## Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Имя бота (макс. 64 символа) |
| `description` | string | No | Описание (макс. 512 символов) |
| `photo` | File | No | Фото бота (JPEG/PNG, макс. 5MB) |
| `photo_url` | string | No | URL фото (альтернатива `photo`) |

---

## Response

### 200 OK — Успех

```json
{
    "name": {"success": true},
    "description": {"success": true},
    "photo": {"success": true}
}
```

### 207 Partial — Частичный успех

```json
{
    "name": {"success": true},
    "photo": {"success": false, "error": "No authenticated userbot available"}
}
```

### 400 Bad Request — Нет полей

```json
{
    "error": "No settings provided. Send name, description, and/or photo."
}
```

---

## Возможные ошибки `photo`

| error | Причина |
|-------|---------|
| `"Photo must be JPEG or PNG"` | Неверный формат файла |
| `"Photo must be 5MB or less"` | Файл слишком большой |
| `"Photo too small (X bytes)"` | Файл поврежден или пустой |
| `"No authenticated userbot available"` | Нет настроенного userbot в админке |
| `"Bot not found: username"` | BotFather не нашел бота |
| `"Cannot determine bot username"` | У бота нет username в БД |

---

## Важные моменты

1. **Время выполнения:** ~5-10 секунд (userbot общается с BotFather)

2. **Формат фото:** Бэкенд автоматически конвертирует PNG → JPEG, убирает прозрачность

3. **Требование:** В Django Admin должен быть настроен `TelegramUserbot`:
   - Django Admin → Messenger Bots → Telegram Userbots
   - Userbot должен быть авторизован (QR Login или SMS)

4. **Celery:** Для работы нужен запущенный Celery worker:
   ```bash
   celery -A config worker -l info
   ```

---

## Пример с обработкой ошибок

```javascript
const handleSubmit = async (values) => {
    const formData = new FormData();
    const initial = initialValuesRef.current;

    if (values.nickname !== initial.nickname) {
        formData.append("name", values.nickname);
    }

    if (values.description !== initial.description) {
        formData.append("description", values.description);
    }

    if (values.croppedAvatar) {
        // Проверка что это реальный File
        if (!(values.croppedAvatar instanceof File)) {
            console.error("croppedAvatar is not a File:", typeof values.croppedAvatar);
            return Notify.error({ text: "Ошибка: фото не является файлом" });
        }

        if (values.croppedAvatar.size < 100) {
            console.error("File too small:", values.croppedAvatar.size);
            return Notify.error({ text: "Ошибка: файл слишком маленький" });
        }

        formData.append("photo", values.croppedAvatar);
    }

    // Если ничего не изменилось
    if ([...formData.keys()].length === 0) {
        return history.push(`/organizations/${orgID}/assistant?mode=edit`);
    }

    try {
        const response = await axios.post(
            `/messenger-bots/telegram/${orgID}/settings/`,
            formData
        );

        // Проверяем результаты по каждому полю
        const results = response.data;

        if (results.photo?.success === false) {
            Notify.error({ text: `Ошибка фото: ${results.photo.error}` });
        }

        if (results.name?.success === false) {
            Notify.error({ text: `Ошибка имени: ${results.name.error}` });
        }

        // Если хоть что-то успешно
        if (results.photo?.success || results.name?.success || results.description?.success) {
            Notify.success({ text: "Настройки обновлены!" });
        }

    } catch (error) {
        console.error("Settings update error:", error);
        Notify.error({ text: "Ошибка при обновлении настроек" });
    }
};
```

---

## Debugging

### Логи бэкенда

```bash
# Django logs
[TG_SETTINGS] POST settings for org_id=101
[TG_SETTINGS] Content-Type: multipart/form-data; boundary=...
[TG_SETTINGS] request.data keys: ['name', 'photo']
[TG_SETTINGS] request.FILES keys: ['photo']
[TG_SETTINGS] Setting photo from file: name=avatar.jpg, size=1765424, content_type=image/jpeg

# Celery logs
[USERBOT_TASK] set_bot_photo started for @my_bot_username
[BOT_FACTORY] ====== SET BOT PHOTO START ======
[BOT_FACTORY] Bot username: @my_bot_username
[BOT_FACTORY] Photo size: 1765424 bytes, type: image/jpeg
[BOT_FACTORY] Sending /setuserpic to BotFather...
[BOT_FACTORY] Final BotFather response: Success! The new profile photo is set...
[BOT_FACTORY] ====== SET BOT PHOTO SUCCESS ======
```

### Проверка на фронте

```javascript
// Перед отправкой
console.log("croppedAvatar:", values.croppedAvatar);
console.log("Is File:", values.croppedAvatar instanceof File);
console.log("Size:", values.croppedAvatar?.size);
console.log("Type:", values.croppedAvatar?.type);
```
