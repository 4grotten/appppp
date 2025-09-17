from django.core.management.base import BaseCommand
from notifications.models import Notification, NotificationSetting
from users.models import User


class Command(BaseCommand):
    help = (
        "Check which notifications would be sent to user's devices and their languages"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "user_id", type=int, help="ID of the user to check notifications for"
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with id {user_id} not found"))
            return

        if not NotificationSetting.objects.filter(user=user).exists():
            self.stdout.write(
                self.style.WARNING(f"No NotificationSetting for user {user_id}")
            )
            return

        notification_setting = NotificationSetting.objects.get(user=user)
        self.stdout.write(self.style.SUCCESS(f"Devices for user {user.email}:"))

        for device in notification_setting.fcm_device.all():
            lang_obj = device.settingstotoken_set.first()
            lang = lang_obj.language if lang_obj else "en"
            self.stdout.write(
                f" - Device {device.id}: type={device.type}, language={lang}, token={device.registration_id[:10]}"
            )

        # Покажем последние 5 уведомлений для пользователя
        self.stdout.write(
            self.style.SUCCESS(f"\nLast 5 notifications for user {user.email}:")
        )
        notifications = Notification.objects.filter(recipient=user).order_by(
            "-created_at"
        )[:5]
        for n in notifications:
            self.stdout.write(f" - Notification {n.id}: type={n.type}, mode={n.mode}")
            self.stdout.write(
                f"   EN: {getattr(n, 'title', '')} / {getattr(n, 'description', '')}"
            )
            self.stdout.write(
                f"   RU: {getattr(n, 'title_ru', '')} / {getattr(n, 'description_ru', '')}"
            )
            self.stdout.write(
                f"   DE: {getattr(n, 'title_de', '')} / {getattr(n, 'description_de', '')}"
            )
