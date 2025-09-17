from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import NotificationSetting, SettingsToToken
from firebase_admin.messaging import Message, Notification

User = get_user_model()


class Command(BaseCommand):
    help = "Test FCM web push for a specific user (dry_run)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user_id", type=int, required=True, help="ID of the user to test push"
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with ID {user_id} does not exist")
            )
            return

        try:
            ns = NotificationSetting.objects.get(user=user)
        except NotificationSetting.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"No NotificationSetting for user {user.username}")
            )
            return

        # Создаём тестовый payload
        title_test = "Hello EN"
        description_test = "This is a test message"
        payload_test = Message(
            notification=Notification(title=title_test, body=description_test),
            data={"test": "123"},
        )

        # Фильтруем веб-устройства
        fcm_web_devices = ns.fcm_device.filter(type="web")
        if not fcm_web_devices.exists():
            self.stdout.write(self.style.WARNING("No web devices found for this user"))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Testing FCM Web Devices for user {user.username}")
        )

        # Логируем устройства и их язык
        for device in fcm_web_devices:
            try:
                lang = device.settingstotoken.language
            except SettingsToToken.DoesNotExist:
                lang = "N/A"
            self.stdout.write(
                f"Device ID: {device.id}, token: {device.registration_id[:10]}..., lang: {lang}"
            )
            # Отправка dry_run
            device.send_message(payload_test, dry_run=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Sent dry_run test to device {device.id} lang={lang}"
                )
            )
