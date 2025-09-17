# Тест пуша веб-устройств

from django.contrib.auth import get_user_model
from notifications.models import NotificationSetting, SettingsToToken
from notifications.services import FCMDeviceSettingsService  # если нужно
from firebase_admin.messaging import Message, Notification

User = get_user_model()

# 1️⃣ Выбираем тестового пользователя
user_id = 1  # поменять на тестового
user = User.objects.get(id=user_id)

# 2️⃣ Берём его NotificationSetting
try:
    ns = NotificationSetting.objects.get(user=user)
except NotificationSetting.DoesNotExist:
    print(f"No NotificationSetting for user {user.username}")
    exit()

# 3️⃣ Создаём тестовый payload
title_test = "Hello EN"
description_test = "This is a test message"
payload_test = Message(
    notification=Notification(title=title_test, body=description_test),
    data={"test": "123"},
)

# 4️⃣ Фильтруем веб-устройства
fcm_web_devices = ns.fcm_device.filter(type="web")

# 5️⃣ Логируем устройства и их язык
print(f"=== Testing FCM Web Devices for user {user.username} ===")
for device in fcm_web_devices:
    try:
        lang = device.settingstotoken.language
    except SettingsToToken.DoesNotExist:
        lang = "N/A"
    print(
        f"Device ID: {device.id}, token: {device.registration_id[:10]}..., lang: {lang}"
    )

# 6️⃣ Отправляем тестовый пуш (dry_run=True, чтобы не спамить)
for device in fcm_web_devices:
    device.send_message(payload_test, dry_run=True)
    print(f"✅ Sent dry_run test to device {device.id} lang={lang}")
