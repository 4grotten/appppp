# Деплой App (EasyCard)

## URL
```
https://test.apofiz.com/EasyCard/
```

## Структура (monorepo)

```
backend/
├── docker-compose.test.yml
├── nginx/
│   └── apofiz.conf          # ← location /EasyCard/ добавлен сюда
└── App/
    ├── Dockerfile
    ├── nginx.conf
    ├── vite.config.ts       # ← base: "/EasyCard/"
    └── src/
```

---

## Часть 1: Пуш кода в GitLab

```bash
cd /home/mioneris/appofiz/backend

# Добавить все изменения
git add App/ nginx/apofiz.conf docker-compose.test.yml

# Коммит
git commit -m "Add EasyCard frontend app"

# Пуш
git push
```

---

## Часть 2: Деплой на сервере

### 2.1 Подключение

```bash
ssh user@your-server-ip
```

### 2.2 Обновление репозитория

```bash
cd /root/projects/backend
git pull
```

### 2.3 Сборка и запуск

```bash
docker-compose -f docker-compose.test.yml build app
docker-compose -f docker-compose.test.yml up -d app
```

### 2.4 Проверка контейнера

```bash
# Статус
docker-compose -f docker-compose.test.yml ps app

# Логи
docker-compose -f docker-compose.test.yml logs app

# Тест локально
curl http://localhost:3001
```

---

## Часть 3: Обновление Nginx

### 3.1 Скопировать обновлённый конфиг

```bash
sudo cp /root/projects/backend/nginx/apofiz.conf /etc/nginx/sites-available/
```

### 3.2 Проверка и перезагрузка

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Часть 4: Тестирование

```bash
# Проверка
curl -I https://test.apofiz.com/EasyCard/
```

Открыть в браузере: `https://test.apofiz.com/EasyCard/`

---

## Обновление приложения

### Локально

```bash
cd /home/mioneris/appofiz/backend
git add App/
git commit -m "Update EasyCard"
git push
```

### На сервере

```bash
cd /root/projects/backend
git pull
docker-compose -f docker-compose.test.yml build app
docker-compose -f docker-compose.test.yml up -d app
```

---

## Troubleshooting

### 404 на /EasyCard/

```bash
# Проверить что контейнер запущен
docker ps | grep app

# Проверить nginx конфиг
sudo nginx -t

# Проверить что location добавлен
grep -A5 "EasyCard" /etc/nginx/sites-available/apofiz.conf
```

### Белая страница / ошибки JS

```bash
# Проверить что base path правильный в vite.config.ts
grep "base" /root/projects/backend/App/vite.config.ts
# Должно быть: base: "/EasyCard/"

# Пересобрать
docker-compose -f docker-compose.test.yml build --no-cache app
docker-compose -f docker-compose.test.yml up -d app
```

### Откат

```bash
docker-compose -f docker-compose.test.yml stop app
docker-compose -f docker-compose.test.yml rm app
```

---

## Полезные команды

```bash
# Логи в реальном времени
docker-compose -f docker-compose.test.yml logs -f app

# Рестарт
docker-compose -f docker-compose.test.yml restart app

# Зайти внутрь контейнера
docker-compose -f docker-compose.test.yml exec app sh
```
